#!/usr/bin/env python
#!BPY
"""Registration info for Blender menus:
Name: 'TreeViewer'
Blender: 232
Group: 'MISC'
Tooltip: 'Visualiza a Cena 3D em forma de ï¿½vore imprimindo apenas o nome dos objetos'
"""
#-----------------------------------------------------------------
#YEAHaieua
# ***** BEGIN GPL LICENSE BLOCK *****
#
# Copyright (C) 2004/: Rodrigo (Spy) Domingues - spy@opengl.com.br, spy@lordspy.mat.br
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****

####################################
# Global Variables
####################################
# Public, you may change these
_exportSelected = True    # If false, exports the entire scene

_safeOverwrite = True     # If false, will overwrite files without asking.

# Private, don't change these
_doc = None
#lista de relacionamentos na ï¿½vore:
#[[Obj,Pai]]
_relations = []
#lista temporaria para armazenar os filhos de um objeto para construir a ï¿½vore
_childs=[]
#A ï¿½vore final
_arvore = []
#lista temporï¿½ia, com as raï¿½es da cena (objetos sem filhos)
_raizes = []
#lista (skip list) contendo o ï¿½dice dos vertices para as faces (entre parenteses indica opcional)
#[[obj,[[face,[[v1,v2,v3(,v4)],...]],[face2,[[v1,v2,v3(,v4)],...]],...]],[obj2,...]]
_indexFaceSet = []
#lista (skip list) contendo os vertices de um objeto
#[[obj,[[v1x,v1y,v1z],[v2x,v2y,v2z],...]],[obj2,[[v1x,v1y,v1z],[v2x,v2y,v2z],...]],...]
_vertexList = []
#lista com os vertices de textura para cada face de cada objeto
_texVertexList = []
#lista com os vertices de normais do objeto (uma por vï¿½tice?)
_normalVertexList = []
#lista com os indices das normais para cada vertice de cada objeto
_normalVertexIndex=[]
#lista com os materiais aplicados a cada objeto
#material=[amb,diff,spec]
#amb, diff e spec sï¿½ listas com 3 valores representando RGB
#[[obj,material],...]
_materialAttr = []
#lista com as texturas para cada objeto
#[[obj,textura],...]
_mattext=[]
#lista com as transformacoes de cada objeto
#transformacao=[rot,loc,scal]
#lista=[[obj,transform],...]
#rotacao em quaternions
_objtransform=[]
#lista com os interpoladores para cada objeto
#[[obj,[IPO]],...]
_interpolators = []
#lista com interpoladores para X3D.
#interpolador=[tipo,[chave],[valores]]
#lista=[obj,[interpoladores]]
_x3dInterpolators=[]
_texVertexIndex=[]
_defs=[]
_matname=[]
_objtimer=[]
_sensor=[]
_fatalError = False
_disableVRML = False
_actions = []
__sensors=[]
__actions=[]
__visibleTimer=[]
global _treeLevel
####################################
# Library dependancies
####################################
import sys
from math import *
from os.path import exists, join
import sets
from sets import * 
try:
	import Blender
	from Blender import Object, NMesh, Lamp, Draw, BGL, Texture, Types, Camera, Image, Window
	from Blender.Window import DrawProgressBar
	from Blender.Mathutils import *
	
except:
  print "Fatal Error! Unable to find Blender modules!"
  print "Are you running this script from within blender?"
  _fatalError = True

#####################################################################
########### Coisas Globais
#####################################################################
filename = ""
def f(name): # file selector callback
	global filename
	filename = name

######################################################################
	
	
def buildrelations():
	DrawProgressBar(0.0, " Constroi Relacionamentos entre objetos da cena")  
	retorno=[]
	for k in Blender.Object.Get():
		if (not k.getParent()):
			retorno.append([k,None])
		else:
			retorno.append([k,k.getParent()]);
	return retorno
	
def findchilds(pai):
	DrawProgressBar(0.0, " Busca Filhos de "+pai.getName())  
	retorno=[]
	for k in buildrelations():
		if k[1]==pai:
			retorno.append(k[0]);
	#print "Os filhos de"
	#print pai
	#print "Sao"
	#print retorno
	return retorno

def findroots():
	DrawProgressBar(0.0, " Busca objetos sem Pai (raizes)")  
	retorno=[]
	for k in buildrelations():
		if (not k[1]):
			retorno.append(k[0])
	#print "raizes achadas"
	#print retorno
	return retorno
	
def hasChilds(pai):
	#print "verificando se:"
	#print pai
	#print "Possui filhos"
	retorno=0
	for k in buildrelations():
		if k[1]==pai:
			retorno=1
	return retorno

def percorre(nodes):
	DrawProgressBar(0.0, " Percorre os dados construindo a árvore")  
	retorno=[]
	if len(nodes)==0:
		return []
	for k in nodes:
		retorno.append([k,percorre(findchilds(k))])
	#print "retornando do percorre:"
	#print retorno
	return retorno
	
############################################################################
###############Constroi a estrutura de ï¿½vore
############################################################################
def buildtree():
	DrawProgressBar(0.0, " Procurando Objetos sem Pai")  
	raizes=findroots()
	retorno=[]
	for k in raizes:
		DrawProgressBar(0.0, " Construindo subarvore de "+k.getName())  
		#print "Inserindo sub arvores de "
		#print k
		retorno.append([k,percorre(findchilds(k))])
	#print "Arvore calculada"
	return retorno

###########################################################################
##############Percorre a arvore e constroi as skiplists
###########################################################################
def imparv(a,niv):
#	if (not a):
#		for l in range(niv):
#			print "--",
#		print ">X"
	for k in a:
#		for i in range(niv):
#			print "--",
#		print k[0]
#		print
		objectdata(k[0])
		imparv(k[1],niv+1)

###########################################################################
##############Recupera os dados de Materiais do Objeto
##############Anexando os dados na SkipList de Materiais
###########################################################################
def materialdata(obj):
	DrawProgressBar(0.0, obj.getName()+" MaterialData")  
#	print "****************************************************************"
#	print "****************Material Data***********************************"
	if(obj.getType()=="Mesh"):
		#print obj.getData().getMaterials(1)
		material=[]
		for m in obj.getData().getMaterials(1):
			if m:
				material=[m.rgbCol,m.specCol,m.getAmb(),1-m.getAlpha(),m.getSpec(),m.getName()+"_MAT"]
				_matname.append(m.getName())
		#		print m.getRGBCol()
		#		print m.getSpecCol()
				texturedata(obj)
			else:
				material=[[0.5,0.5,0.5],[0.5,0.5,0.5],[0.5,0.5,0.5],0.0,0.0,obj.getName()+"_MAT"]
		_materialAttr.append([obj,material])

##########################################################################
#############retorna uma lista com os ï¿½dices dos 3 vï¿½tices 
############# De uma Face 
##########################################################################
def getVertexIndex(vertices,face):
	indices=[]
	for i in face.v:
		indices.append(vertices.index(i))
#		indice=0
#		for v in vertices:
#			if ((v[0]==i.co[0])and(v[1]==i.co[1])and(v[2]==i.co[2])):
#				indices.append(indice)
#				break
#			indice+=1
	return indices

##########################################################################
############ Retorna o ï¿½dice de uma normal para um vï¿½tice
##########################################################################
def getNormalIndex(normalList,vertex):
	offset=0
	for n in normalList:
		if((n[0]==vertex.no[0]) and (n[1]==vertex.no[1]) and (n[2]==vertex.no[2])):
			return offset
		offset+=1

def getCenter(obj):
	if(obj.getData()):
		if obj.getBoundBox():
			bb=obj.getBoundBox()
			cx=(bb[4][0]-bb[0][0])/2+bb[0][0]
			cy=(bb[2][1]-bb[1][1])/2+bb[1][1]
			cz=(bb[1][2]-bb[0][2])/2+bb[0][2]
		else:
			return getloc(obj.loc)
	else:
		print "Objeto sem dado"
	return [cx,cy,cz]


def quat2aa(quat):
	quat.normalize()
	w=quat[0]
	ang=0
	ret=[]
	if(abs(w)<1):
		ang=2*acos(w)
		divis=sqrt(1-(w*w))
		ret=[quat[1]/divis,quat[2]/divis,quat[3]/divis,ang]
	else:
		ret=[0,0,0,0]
	return ret
def ajusta(matriz):
	for i in matriz:
		linha=[]
		for j in i:
			if abs(j)<0.00001:
				j=0.0000

##########################################################################
########## Recupera os dados de Transformaï¿½o e 
########## Anexa os dados na SkipList de Transformaï¿½o
##########################################################################
def transformdata(obj):
#	print "****************************************************************"
#	print "****************Transform Data**********************************"
	DrawProgressBar(0.0, obj.getName()+" TransformData")  
	obr=obj.getEuler();
	obrm=obr.toMatrix()
	obs=obj.getSize()
	p=None
	q=[]
	s=[]
	if obj.getParent():
		#Rotação Diferencial:
		#Rotação no Blender é sempre absoluta, assim
		# Rf=RA*(Rpai)^(-1)
		pr=obj.getParent().getEuler()
#		print "rotacao euler do pai de "+obj.getName()
#		print pr
		prm=pr.toMatrix()
		prm.invert()
		##########################################################################
		# Verificar se o Python Multiplica essas matrizes
#		rm=prm*obrm
		rm=obj.matrixLocal.rotationPart()
		##########################################################################
		re=rm.toQuat()
		r=quat2aa(re)
#		r=euler2AxisAngle(re)
		ps=obj.getParent().getSize()
		s=[obs[0]/ps[0],obs[1]/ps[1],obs[2]/ps[2]]
		mo=obj.mat
		mp=obj.getParent().mat
		z=mo-mp
		p=[z[3][0],z[3][1],z[3][2]]
##########################################################	
#		c=getCenter(obj)
#		pc=getCenter(obj.getParent())
#		p=[c[0]-pc[0],c[1]-pc[1],c[2]-pc[2]]
##########################################################
#		p=[obj.loc[0]-obj.getParent().loc[0],obj.loc[1]-obj.getParent().loc[1],obj.loc[2]-obj.getParent().loc[2]]
#		p=[obj.loc[0]+obj.getParent().loc[0],obj.loc[1]+obj.getParent().loc[1],obj.loc[2]+obj.getParent().loc[2]]
#		p=getloc(obj.getParent().loc)
#		p=getloc(obj.loc)
	else:
		s=obs
		mo=obj.mat
		r=euler2AxisAngle(obr)
		p=[mo[3][0],mo[3][1],mo[3][2]]
#		p=getCenter(obj)
	dl=[obj.dLocX,obj.dLocY,obj.dLocZ]
#	print dl
#	print p
	#print "pos=%.3f, %.3f, %.3f"%(obj.LocX,obj.LocY,obj.LocZ)
	transform=[r,p,s,dl]
	_objtransform.append([obj,transform])

#########################################################################
######### Recupera os dados de Malha e constrï¿½ as skiplists.
######### Dados de Malha Sï¿½:
############# Faces: Recupera os ï¿½dices para os vï¿½tices
#############  FacesIndices: Os ï¿½dices para os vertices. Sao anexados
#################### A uma SkipList
############# Vertices: Todos os Vertices do objeto
################### Anexados ï¿½skiplist de vï¿½tices
############# Normais: Todas as Normais dos Objetos
################### Anexadas ï¿½uma SkipList
############# NormaisIndex: Indices de normais dos vertices
################### Anexadas a uma skiplist
############# CoordTex: Coordenadas de textura para as faces
################### Anexadas a uma SkipList
#########################################################################
def meshdata(obj):
	DrawProgressBar(0.0, obj.getName()+" MeshData")  
#	print "****************************************************************"
#	print "****************Mesh Data***********************************"
	if(obj.getType()=="Mesh"):
		malha=obj.getData()
		faces=[]
		facesIndices=[]
		vertices=[]
		texvertices=[]
		normals=[]
		normalsindex=[]
		#calcula a lista de vertices do objeto
		#calcula o indice das normais dos vertices
		vertices=malha.verts
		for v in malha.verts:
			normals.append(v.no)
		#calcula as faces e as normais de cada vertice
		#o indice das normais pra cada vertice ainda estah porco
		for f in malha.faces:
			faces.append(f)
			for v in f.v:
				normalsindex.append(malha.verts.index(v))
		#calcula o indice dos vertices de uma malha
		for f in malha.faces:
			ind=getVertexIndex(malha.verts,f)
			facesIndices.append(ind)
#		print "Numero de indices:"
#		print len(facesIndices)
		#constroi os objetos para as skiplists
		#objetos de indices
#		facesobjeto=[]
#		facesobjeto.append([obj,facesIndices])
		_indexFaceSet.append([obj,facesIndices])
		#objetos de vï¿½tices
#		verticesobjeto=[]
#		verticesobjeto.append([obj,vertices])
		_vertexList.append([obj,vertices])
		#objetos de normais
		_normalVertexList.append([obj,normals])
		_normalVertexIndex.append([obj,normalsindex])
		#objetos de indices de normais
		#calcula as coordenadas UV de cada vï¿½tice
		if (malha.hasFaceUV):
			indtexvertex=[]
			uvindex=0
			for f in malha.faces:
#				print "Vertices de Textura"
				for v in f.uv:
					texvertices.append(v)
#			for f in malha.faces:
#				for v in f.uv:
#					indtexvertex.append(getTexIndex(f,texvertices))
			ind=0
			for f in malha.faces:
				tvi=[]
				for v in f.uv:
					tvi.append(ind)
					ind+=1
				indtexvertex.append(tvi)
			_texVertexList.append([obj,texvertices])
			_texVertexIndex.append([obj,indtexvertex])
		#calcula os objetos para as skiplists de vï¿½tices de textura

		
def getTexIndex(face,texvlist):
	index=[]
	indice=0
	for uv in face.uv:
		indice=0
		for v in texvlist:
#			if (uv[0]==v[0]) and (uv[1]==v[1]):
#				index.append(indice)
#				break
			indice+=1
	return index
######################################################################
################ Recupera os dados de Textura e
################ Os anexa ï¿½SkipList de Texturas
######################################################################
def texturedata(objeto):
	DrawProgressBar(0.0, objeto.getName()+" TextureData")  
#	print "****************************************************************"
#	print "****************Texture Data***********************************"
#	print "A Desenvolver"
	objtex=[]
	mat=objeto.getData().getMaterials(1)
	arqimg=None
	for m in mat:
		texturas=m.getTextures()
		for t in texturas:
			if t:
#				print t
#				print t.tex.getName()
				if t.tex:
					arqimg=t.tex.getImage()
					if arqimg:
#						print arqimg.getFilename()
#						print arqimg.getName()
 						objtex=[objeto,"/home/spy/"+arqimg.getName()]
	if arqimg:
		_mattext.append(objtex)

def actiondata(obj):
	DrawProgressBar(0.0, obj.getName()+" actiondata")  
	objactions=[obj]
	thisactions=[]
	objactions.append(thisactions)
	_actions.append(objactions)
		
#####################################################################
############# Apenas ï¿½um redirecionador, til para o X3D
#####################################################################
def appearancedata(obj):
	DrawProgressBar(0.0, obj.getName()+" appearanceData")  
#	print "****************************************************************"
#	print "****************Appearance Data***********************************"
#	print
	materialdata(obj)

####################################################################
############ Dados de Objetos, chama as rotinas para criaï¿½o das
############ SkipLists
####################################################################
def objectdata(obj):
	DrawProgressBar(0.0, obj.getName()+" ObjectData")  

#	print "****************************************************************"
#	print "****************Object ",
#	print obj.getName(),
#	print " Data***********************************"
#	print obj.getData()
	transformdata(obj)
	appearancedata(obj)
	curvedata(obj)
	meshdata(obj)
	actiondata(obj)
#	print "****************************************************************"
#	print "****************SkipLists Data***********************************"
#	if hasTransform(obj)==1:
#		print "****************Transform Data Skip************************************"
#		print getSkipData(obj,_objtransform)
#	if hasAnimation(obj)==1:
#		print "****************X3D AnimationData Skip************************************"
#		print getSkipData(obj,_x3dInterpolators)
#		print "****************IPO Skip************************************"
#		print getSkipData(obj,_interpolators)
#	if hasMaterial(obj)==1:
#		print "****************Material Skip************************************"
#		print getSkipData(obj,_materialAttr)
#	if hasTexture(obj)==1:
#		print "****************Texture Skip************************************"
#		print getSkipData(obj,_mattext)
#	tipo=type(obj.getData())
#	if tipo==Types.NMeshType:
#		print "****************IndexFaceSet Skip************************************"
#		print "numero de faces=",
#		print len(getSkipData(obj,_indexFaceSet)[1])
#		print getSkipData(obj,_indexFaceSet)
#		print "****************VertexList Skip************************************"
#		print "numero de vertices=",
#		print len(getSkipData(obj,_vertexList)[1])
#		print getSkipData(obj,_vertexList)
#		print "****************TexVertexList Skip************************************"
#		print "numVertText=",
#		print len(getSkipData(obj,_texVertexList)[1])
#		print getSkipData(obj,_texVertexList)
#		print "****************NormalVertexIndex Skip************************************"
#		print "numero de indices de normais=",
#		print len(getSkipData(obj,_normalVertexIndex)[1])
#		print getSkipData(obj,_normalVertexIndex)
#		print "****************NormalList Skip************************************"
#		print "Numero de normais=",
#		print len(getSkipData(obj,_normalVertexList)[1])
#		print getSkipData(obj,_normalVertexList)
	
#####################################################################
############ Rotina para se recuperar um dado em uma curva em um 
############ Determinado tempo. O dado em si jï¿½estï¿½calculado devido
############ Aos quadros chave. Dados que nï¿½ estï¿½ calculados
############ Devem utilizar a rotina seguinte
#####################################################################
def buscaDadoEmCurva(curva,tempo):
	for p in curva.getPoints():
		if p.getPoints()[0]==tempo:
			return p.getPoints()[1]

#####################################################################
######## Rotina auxiliar para cï¿½culo dos valores dos quadros chaves
######## Retorna um valor para a curva em um determinado tempo quando
######## Nï¿½ hï¿½um quadro chave na curva no tempo especificado
#####################################################################
def calculaParaCurva(tempo,curva):
	return curva.evaluate(tempo)

	
#####################################################################
######## Recupera os dados do interpolador de posiï¿½o e os
######## coloca em uma SkipList. Obs. ï¿½necessï¿½io verificar se
######## O interpolador de posiï¿½o usa coordenadas relativas ou
######## Absolutas. Essa rotina calcula a transformaï¿½o relativa
#####################################################################
def buildDeltaPositionInterpolator(cx,cy,cz):
	start=Blender.Scene.getCurrent().getRenderingContext().startFrame()
	end=Blender.Scene.getCurrent().getRenderingContext().endFrame()
#	print "quadros de",
#	print start,
#	print "a"
#	print end
	interp=[]
	chave=[]
	valores=[]
	interptemp=[]
	interpX=[]
	interpY=[]
	interpZ=[]
	if cx:
		for vx in cx.getPoints():
			if(vx.getPoints()[0] not in interptemp):
				interptemp.append(vx.getPoints()[0])
			interpX.append(vx.getPoints()[0])
	if cy:
		for vy in cy.getPoints():
			if(vy.getPoints()[0] not in interptemp):
				interptemp.append(vy.getPoints()[0])
			interpY.append(vy.getPoints()[0])
	if cz:
		for vz in cz.getPoints():
			if(vz.getPoints()[0] not in interptemp):
				interptemp.append(vz.getPoints()[0])
			interpZ.append(vz.getPoints()[0])
#	print interptemp
	interptemp.sort()
#	print interptemp
	chave2=interptemp
	chave=[x/end for x in interptemp]
	#busca os valores para cada dado, se nï¿½ houver, recalcula
	pontosX=[]
	pontosY=[]
	pontosZ=[]
	for t in chave2:
		if cx:
			if t not in interpX:
				pontosX.append(calculaParaCurva(t,cx))
			else:
				pontosX.append(buscaDadoEmCurva(cx,t))
		else:
				pontosX.append(0);
		if cy:
			if t not in interpY:
				pontosY.append(calculaParaCurva(t,cy))
			else:
				pontosY.append(buscaDadoEmCurva(cy,t))
		else:
				pontosY.append(0);
		if cz:
			if t not in interpZ:
				pontosZ.append(calculaParaCurva(t,cz))
			else:
				pontosZ.append(buscaDadoEmCurva(cz,t))
		else:
				pontosZ.append(0);
	valores=[]
	for p in range(len(pontosX)):
		valores.append([pontosX[p],pontosY[p],pontosZ[p]])
	interp=["DeltaPositionInterpolator",chave,valores]
	return interp
 
#####################################################################
######## Recupera os dados do interpolador de posiï¿½o e os
######## coloca em uma SkipList. Obs. ï¿½necessï¿½io verificar se
######## O interpolador de posiï¿½o usa coordenadas relativas ou
######## Absolutas. Essa rotina calcula a transformaï¿½o Absoluta
#####################################################################
def buildPositionInterpolator(cx,cy,cz):
	start=Blender.Scene.getCurrent().getRenderingContext().startFrame()
	end=Blender.Scene.getCurrent().getRenderingContext().endFrame()
#	print "quadros de",
#	print start,
#	print "a"
#	print end
	interp=[]
	chave=[]
	valores=[]
	interptemp=[]
	interpX=[]
	interpY=[]
	interpZ=[]
	if cx:
		for vx in cx.getPoints():
			if(vx.getPoints()[0] not in interptemp):
				interptemp.append(vx.getPoints()[0])
			interpX.append(vx.getPoints()[0])
	if cy:
		for vy in cy.getPoints():
			if(vy.getPoints()[0] not in interptemp):
				interptemp.append(vy.getPoints()[0])
			interpY.append(vy.getPoints()[0])
	if cz:
		for vz in cz.getPoints():
			if(vz.getPoints()[0] not in interptemp):
				interptemp.append(vz.getPoints()[0])
			interpZ.append(vz.getPoints()[0])
	interptemp.sort()
	chave2=interptemp
	chave=[x/end for x in interptemp]
	#busca os valores para cada dado, se nï¿½ houver, recalcula
	pontosX=[]
	pontosY=[]
	pontosZ=[]
	for t in chave2:
		if cx:
			if t not in interpX:
				pontosX.append(calculaParaCurva(t,cx))
			else:
				pontosX.append(buscaDadoEmCurva(cx,t))
		else:
				pontosX.append(0);
		if cy:
			if t not in interpY:
				pontosY.append(calculaParaCurva(t,cy))
			else:
				pontosY.append(buscaDadoEmCurva(cy,t))
		else:
				pontosY.append(0);
		if cz:
			if t not in interpZ:
				pontosZ.append(calculaParaCurva(t,cz))
			else:
				pontosZ.append(buscaDadoEmCurva(cz,t))
		else:
				pontosZ.append(0);
	valores=[]
	for p in range(len(pontosX)):
		valores.append([pontosX[p],pontosY[p],pontosZ[p]])
	interp=["PositionInterpolator",chave,valores]
	return interp

#####################################################################
######## Recupera os dados do interpolador de orientaï¿½o e os
######## coloca em uma SkipList. Obs. O interpolador de Orientaï¿½o
######## Do X3D utiliza coordenadas Absolutas. Essa rotina nï¿½
######## ï¿½vï¿½ida ou necessita-se calcular as posiï¿½es absolutas
#####################################################################
def buildDeltaOrientationInterpolator(rx,ry,rz):
	start=Blender.Scene.getCurrent().getRenderingContext().startFrame()
	end=Blender.Scene.getCurrent().getRenderingContext().endFrame()
#	print "quadros de",
#	print start,
#	print "a"
#	print end
	interp=[]
	chave=[]
	valores=[]
	interptemp=[]
	interpX=[]
	interpY=[]
	interpZ=[]
	if rx:
		for vx in rx.getPoints():
			if(vx.getPoints()[0] not in interptemp):
				interptemp.append(vx.getPoints()[0])
			interpX.append(vx.getPoints()[0])
	if ry:
		for vy in ry.getPoints():
			if(vy.getPoints()[0] not in interptemp):
				interptemp.append(vy.getPoints()[0])
			interpY.append(vy.getPoints()[0])
	if rz:
		for vz in rz.getPoints():
			if(vz.getPoints()[0] not in interptemp):
				interptemp.append(vz.getPoints()[0])
			interpZ.append(vz.getPoints()[0])
	interptemp.sort()
	chave2=interptemp
	chave=[x/end for x in interptemp]
	#busca os valores para cada dado, se nï¿½ houver, recalcula
	pontosX=[]
	pontosY=[]
	pontosZ=[]
	for t in chave2:
		if rx:
			if t not in interpX:
				pontosX.append(calculaParaCurva(t,rx))
			else:
				pontosX.append(buscaDadoEmCurva(rx,t))
		else:
				pontosX.append(0);
		if ry:
			if t not in interpY:
				pontosY.append(calculaParaCurva(t,ry))
			else:
				pontosY.append(buscaDadoEmCurva(ry,t))
		else:
				pontosY.append(0);
		if rz:
			if t not in interpZ:
				pontosZ.append(calculaParaCurva(t,rz))
			else:
				pontosZ.append(buscaDadoEmCurva(rz,t))
		else:
				pontosZ.append(0);
	valorestemp=[]
	valores=[]
	for p in range(len(pontosX)):
		valorestemp.append([pontosX[p],pontosY[p],pontosZ[p]])
	#valorestemp estï¿½em ï¿½gulos, precisa-se de quaternion
	for a in valorestemp:
		e=Euler(a)
		aa=e.toQuat()
#		valores.append(aa)
		valores.append(euler2AxisAngle(a))
	interp=["OrientationInterpolator",chave,valores]
	return interp

	
#####################################################################
######## Recupera os dados do interpolador de orientaï¿½o e os
######## coloca em uma SkipList. Obs. O interpolador de Orientaï¿½o
######## Do X3D utiliza coordenadas Absolutas. 
#####################################################################
def buildOrientationInterpolator(rx,ry,rz):
	start=Blender.Scene.getCurrent().getRenderingContext().startFrame()
	end=Blender.Scene.getCurrent().getRenderingContext().endFrame()
#	print "quadros de",
#	print start,
#	print "a"
#	print end
	interp=[]
	chave=[]
	valores=[]
	interptemp=[]
	interpX=[]
	interpY=[]
	interpZ=[]
	if rx:
		for vx in rx.getPoints():
			if(vx.getPoints()[0] not in interptemp):
				interptemp.append(vx.getPoints()[0])
			interpX.append(vx.getPoints()[0])
	if ry:
		for vy in ry.getPoints():
			if(vy.getPoints()[0] not in interptemp):
				interptemp.append(vy.getPoints()[0])
			interpY.append(vy.getPoints()[0])
	if rz:
		for vz in rz.getPoints():
			if(vz.getPoints()[0] not in interptemp):
				interptemp.append(vz.getPoints()[0])
			interpZ.append(vz.getPoints()[0])
	interptemp.sort()
	chave2=interptemp
	chave=[x/end for x in interptemp]
	#busca os valores para cada dado, se nï¿½ houver, recalcula
	pontosX=[]
	pontosY=[]
	pontosZ=[]
	for t in chave2:
		if rx:
			if t not in interpX:
				pontosX.append(calculaParaCurva(t,rx))
			else:
				pontosX.append(buscaDadoEmCurva(rx,t))
		else:
			pontosX.append(0);
		if ry:
			if t not in interpY:
				pontosY.append(calculaParaCurva(t,ry)*10)
			else:
				pontosY.append(buscaDadoEmCurva(ry,t)*10)
		else:
				pontosY.append(0);
		if rz:
			if t not in interpZ:
				pontosZ.append(calculaParaCurva(t,rz))
			else:
				pontosZ.append(buscaDadoEmCurva(rz,t))
		else:
				pontosZ.append(0);
	valorestemp=[]
	valores=[]
	for p in range(len(pontosX)):
		valorestemp.append([pontosX[p],pontosY[p],pontosZ[p]])
	#valorestemp estï¿½em ï¿½gulos, precisa-se de quaternion
	for a in valorestemp:
		e=Euler(a)
		aa=e.toQuat()
#		valores.append(aa)
		valores.append(euler2AxisAngle(a))
	interp=["OrientationInterpolator",chave,valores]
	return interp
#####################################################################
######## Recupera os dados de animaï¿½o e os coloca em duas SkipLists
######## Uma para uso posterior, colocando os objetos IPO's e outra
######## Especï¿½ica para uso no X3D (isso ï¿½ calculando chaves e
######## Valores das curvas do IPO)
#####################################################################
def curvedata(obj):
	DrawProgressBar(0.0, obj.getName()+" CurveData")  
#	print "****************************************************************"
#	print "************* Animation Data ***********************************"
	iponame=""
	if obj.getIpo():
		_interpolators.append([obj,obj.getIpo()])
		iponame=obj.getIpo().getName()
#		print obj.getIpo()
		posInterp=0
		rotInterp=0
		dposInterp=0
		drotInterp=0
		interptemp=[]
		interpolador=[obj]
		for curvas in obj.getIpo().getCurves():
			interp=[]
			nome=curvas.getName()
#			print nome
#			print curvas.getInterpolation()
			if (((nome=="dLocX") or (nome=="dLocY") or (nome=="dLocZ")) and (dposInterp==0)):
				DrawProgressBar(0.0, obj.getName()+" DPos")  
				curva0=obj.getIpo().getCurve("dLocX")
				curva1=obj.getIpo().getCurve("dLocY")
				curva2=obj.getIpo().getCurve("dLocZ")
				interp=buildDeltaPositionInterpolator(curva0,curva1,curva2)
				dposInterp=1
				
			if (((nome=="LocX") or (nome=="LocY") or (nome=="LocZ")) and (posInterp==0)):
				DrawProgressBar(0.0, obj.getName()+" Pos")  
				curva0=obj.getIpo().getCurve("LocX")
				curva1=obj.getIpo().getCurve("LocY")
				curva2=obj.getIpo().getCurve("LocZ")
				interp=buildPositionInterpolator(curva0,curva1,curva2)
				posInterp=1
				
			if (((nome=="dRotX") or (nome=="dRotY") or (nome=="dRotZ")) and (drotInterp==0)):
				DrawProgressBar(0.0, obj.getName()+" DOri")  
				curva0=obj.getIpo().getCurve("dRotX")
				curva1=obj.getIpo().getCurve("dRotY")
				curva2=obj.getIpo().getCurve("dRotZ")
				interp=buildDeltaOrientationInterpolator(curva0,curva1,curva2)
				drotInterp=1
			
			if (((nome=="RotX") or (nome=="RotY") or (nome=="RotZ")) and (rotInterp==0)):
				DrawProgressBar(0.0, obj.getName()+" Ori")  
				curva0=obj.getIpo().getCurve("RotX")
				curva1=obj.getIpo().getCurve("RotY")
				curva2=obj.getIpo().getCurve("RotZ")
				interp=buildOrientationInterpolator(curva0,curva1,curva2)
				rotInterp=1
			if interp:
				interptemp.append(interp)
#			print " Pontos [X,Y] = [Tempo,Valor] "
#			for pontosBezier in curvas.getPoints():
#				print pontosBezier.getPoints()
		interpolador.append(interptemp)
		_x3dInterpolators.append(interpolador)

#####################################################################
#########	Nï¿½ lembro pq coloquei isso...
#####################################################################
def printtree():
	arv=buildtree()
	print "|"
	imparv(arv,0)

#######################################################################
#########  Rotina para conversï¿½ de ï¿½gulos de rotaï¿½o para quaternion
#######################################################################
def euler2AxisAngle(rot):
  c = [ cos(rot[0]/2.0), cos(rot[1]/2.0), cos(rot[2]/2.0) ]
  s = [ sin(rot[0]/2.0), sin(rot[1]/2.0), sin(rot[2]/2.0) ]
  
  a = 2*acos( c[0]*c[1]*c[2] + s[0]*s[1]*s[2] )
  z = c[0]*c[1]*s[2] - s[0]*s[1]*c[2]
  y = c[0]*s[1]*c[2] + s[0]*c[1]*s[2]
  x = s[0]*c[1]*c[2] - c[0]*s[1]*s[2]

  if( abs(a) < 0.0001 ): a = 0
  if( abs(x) < 0.0001 ): x = 0
  if( abs(y) < 0.0001 ): y = 0
  if( abs(z) < 0.0001 ): z = 0
  
  len = sqrt( x*x + y*y + z*z )
  if( abs(len) > 0.0001 ):
    x /= len
    y /= len
    z /= len
  return [ x, y, z, a ]
#####################################################################
############## Rotina que converte a tupla de localizaï¿½o para
############## uma lista
#####################################################################
def getloc(l):
	return [l[0],l[1],l[2]]

#####################################################################
############# Rotina que converte a tupla de escala para uma lista
#####################################################################
def getsize(s):
	return [s[0],s[1],s[2]]

#####################################################################
############# Rotina que verifica uma skiplist para certificar-se que
############# Um objeto possui transformacoes
#####################################################################
def hasTransform(obj):
	for o in _objtransform:
		if o:
			if o[0]==obj:
				return 1
	return 0
#####################################################################
########### Rotina que verifica se um objeto possui ação
########### Serve para colocar as ações nos objetos (principalmente)
########### Os cubos Iconográficos.
#####################################################################
def hasAction(obj):
	l=obj.getAllProperties()
	for k in l:
		if k.name=="prop":
			return 1
	return 0

def isCubeIcon(obj):
	l=obj.getAllProperties()
	for k in l:
		if k.name=="prop1":
			return 1
	return 0
#####################################################################
############# Rotina que verifica uma skiplist para certificar-se que
############# Um objeto possui animaï¿½o
#####################################################################
def hasAnimation(obj):
	for o in _x3dInterpolators:
		if o:
			if o[0]==obj:
				return 1
	return 0

#####################################################################
########### Rotina que verifica se um objeto possui material atravï¿½
########### De uma SkipList
#####################################################################
def hasMaterial(obj):
	for o in _materialAttr:
		if o:
			if o[0]==obj:
				return 1
	return 0

#####################################################################
########## Rotina que verifica se um objeto possui textura atravï¿½
########## de uma SkipList
#####################################################################
def hasTexture(obj):
	for o in _mattext:
		if o:
			if o[0]==obj:
				return 1
	return 0

#####################################################################
############ Rotinas para escrever um arquivo X3D
#####################################################################
def writeAnimationNode(node,_treeLevel):
	obj=node[0]
	DrawProgressBar(0.0, obj.getName()+" Escreve No de animacao")  
	interpdata=getSkipData(obj,_x3dInterpolators)
	print "<!-- ************************************************************"
	print interpdata
	print "*************************************************** -->"
	for i in range(_treeLevel):
		print "	",
	for ips in interpdata[1]:
		if ips[0]=="PositionInterpolator":
			print "<PositionInterpolator DEF=\""+obj.getName()+"_PosInterp\" key=\"",
			for k in ips[1]:
				print "%.3f "%(k),
			print "\" keyValue=\"",
			for kv in ips[2]:
				print "%.3f %.3f %.3f, "%(kv[0],kv[1],kv[2]),
			print "\"/>"
		if ips[0]=="DeltaPositionInterpolator":
			print "<PositionInterpolator DEF=\""+obj.getName()+"_DPosInterp\" key=\"",
			for k in ips[1]:
				print "%.3f "%(k),
			print "\" keyValue=\"",
			for kv in ips[2]:
				print "%.3f %.3f %.3f, "%(kv[0]+obj.loc[0],kv[1]+obj.loc[1],kv[2]+obj.loc[2]),
			print "\"/>"
		if ips[0]=="OrientationInterpolator":
			print "<OrientationInterpolator DEF=\""+obj.getName()+"_RotInterp\" key=\"",
			for k in ips[1]:
				print "%.3f "%(k),
			print "\" keyValue=\"",
			for kv in ips[2]:
				print "%.3f %.3f %.3f %.3f, "%(kv[0],kv[1],kv[2],kv[3]),
			print "\"/>"
	
def writeAppearanceNode(node,_treeLevel):
	obj=node[0]
	DrawProgressBar(0.0, obj.getName()+" Escreve no de aparencia")  
	mat=getSkipData(obj,_materialAttr)
	for i in range(_treeLevel):
		print "	",
	print "<Appearance>"
	_treeLevel+=1
	for i in range(_treeLevel):
		print "	",
#	if mat[1][5] in _defs:
#		print "<Material USE=\""+mat[1][5]+"\"/>"
#	else:
	if (obj.Layer & 1):
		DrawProgressBar(0.0, obj.getName()+" Objeto Visivel de inicio")  
		print "<Material DEF=\""+obj.getName()+"_MAT\" diffuseColor=\"%.3f %.3f %.3f\" ambientIntensity=\"%.3f\" specularColor=\"%.3f %.3f %.3f\" shininess=\"%.3f\" transparency=\"%.3f\"/>"%(mat[1][0][0],mat[1][0][1],mat[1][0][2],mat[1][2],mat[1][1][0],mat[1][1][1],mat[1][1][2],mat[1][4],mat[1][3])
	else:
		DrawProgressBar(0.0, obj.getName()+" Invisivel de Inicio")  
		print "<Material DEF=\""+obj.getName()+"_MAT\" diffuseColor=\"%.3f %.3f %.3f\" ambientIntensity=\"%.3f\" specularColor=\"%.3f %.3f %.3f\" shininess=\"%.3f\" transparency=\"100.0\"/>"%(mat[1][0][0],mat[1][0][1],mat[1][0][2],mat[1][2],mat[1][1][0],mat[1][1][1],mat[1][1][2],mat[1][4])
#		_defs.append(mat[1][5])
	
#########################################################################
#########	Bloco de Textura, funciona, mas tenho que arrumar o
######### problema das coordenadas de textura.
#########################################################################
	if(hasTexture(obj)==1):
		imgtex=getSkipData(obj,_mattext)
		for i in range(_treeLevel):
			print "	",
		print "<ImageTexture  url='\""+imgtex[1]+"\"'/>"
	_treeLevel-=1
	for i in range(_treeLevel):
		print "	",
	print "</Appearance>"

def writeNewGeomNode(node,_treeLevel):
	obj=node[0]
	DrawProgressBar(0.0, obj.getName()+" Escreve No de geometria")  
	facesInd=getSkipData(obj,_indexFaceSet)
	vertsLst=getSkipData(obj,_vertexList)
	normLst=getSkipData(obj,_normalVertexList)
	normIndLst=getSkipData(obj,_normalVertexIndex)
	tvertex=getSkipData(obj,_texVertexList)
	tvindex=getSkipData(obj,_texVertexIndex)
	for i in range(_treeLevel):
		print "	",
	print "<IndexedFaceSet DEF=\""+obj.getData().name+"_FACES\" coordIndex=\"",
	for fi in facesInd[1]:
		print "%d %d %d -1"%(fi[0],fi[1],fi[2]),
	if (hasTexture(obj)):
		print "\" texCoordIndex=\"",
		for uvi in tvindex[1]:
			print "%d %d %d -1"%(uvi[0],uvi[1],uvi[2]),
	print "\" normalPerVertex=\"true\" solid=\"true\" ",
	print "normalIndex=\"",
	count=0
	for ni in normIndLst[1]:
		print "%d"%(ni),
		if count==2:
			print "-1",
			count=-1
		count+=1
	print "\" ccw=\"true\">"
	_treeLevel+=1
######################################################################################
#############	Bloco de Coordenadas de Textura. Funciona, mas ainda tenho
#############	que descobrir como funciona o TexCoordIndex do nï¿½IndexedFaceSet
######################################################################################
	if (hasTexture(obj)):
		for i in range(_treeLevel):
			print "	",
		print "<TextureCoordinate  DEF=\"",
		print obj.getName(),
		print "_TEX\" points=\"",
		for tv in tvertex[1]:
			print "%.3f %.3f,"%(tv[0],tv[1]),
		print "\"/>"
	for i in range(_treeLevel):
		print "	",
	print "<Coordinate DEF=\"",
	print obj.getName(),
	print "_VERTS\" point=\"",
	for v in vertsLst[1]:
		print "%.3f %.3f %.3f,"%(v[0],v[1],v[2]),
	print "\"/>"
	for i in range(_treeLevel):
		print "	",
	print "<Normal vector=\"",
	for n in normLst[1]:
		print "%.3f %.3f %.3f,"%(n[0],n[1],n[2]),
	print "\"/>"
	_treeLevel-=1
	for i in range(_treeLevel):
		print "	",
	print "</IndexedFaceSet>"
	_defs.append(obj.getData().name)

def writeGeometryNode(node,_treeLevel):
	obj=node[0]
	DrawProgressBar(0.0, obj.getName()+" Usa No de geometria")  
	if obj.getData().name not in _defs:
		writeNewGeomNode(node,_treeLevel)
	else:
		for i in range(_treeLevel):
			print "	",
		print "<IndexedFaceSet USE=\""+obj.getData().name+"_FACES\"/>"

def writeVisibilityNodes(obj):
	if (obj.getData()):
		print "<ScalarInterpolator DEF=\""+obj.getName()+"_Inv\" key=\" 0.00  0.01  \" keyValue=\" 0.0, 1.0\"/>"
		print "<ScalarInterpolator DEF=\""+obj.getName()+"_Vis\" key=\" 0.00  0.01  \" keyValue=\" 1.0, 0.0\"/>"
		__visibleTimer.append(obj.getName())

def writeTransformNode(node,_treeLevel):
	obj=node[0]
	DrawProgressBar(0.0, obj.getName()+" Escreve No de Transformacao")  
	skip=getSkipData(obj,_objtransform)
	for i in range(_treeLevel):
	 print "	",
	print "<Transform DEF=\""+obj.getName()+"_OBJ"+"\" translation=\"%.3f %.3f %.3f\""%(skip[1][1][0],skip[1][1][1],skip[1][1][2]),
	print " scale=\"%.3f %.3f %.3f\""%(skip[1][2][0],skip[1][2][1],skip[1][2][2]),
	print " scaleOrientation=\"1.0 0.0 0.0 0.0\"",
	print " rotation=\"%.3f %.3f %.3f %.3f\">"%(skip[1][0][0],skip[1][0][1],skip[1][0][2],skip[1][0][3])
	_treeLevel+=1
	writeVisibilityNodes(obj)
	if(hasAnimation(obj)==1):
		writeAnimationNode(node,_treeLevel)
		__sensors.append(obj)
		#####################################################################
		#Não tinha no original pq a jinx não suporta
		#comentar essa área e descomentar o writetouchsensor no initX3D
		# Colocado o cubo aqui para processamento pela da JINX
		#####################################################################
		
	if(hasAction(obj)==1):
		__actions.append(obj)
		print "<Transform DEF=\""+obj.getName()+"_CUBE"+"\" translation=\"0.0 0.0 0.0\" scale=\"1.0 1.0 1.0\" scaleOrientation=\"1.0 0.0 0.0 0.0\">"
		escala=getSize(obj)
		print "<TouchSensor DEF=\""+obj.getName()+"_TOUCH\"/>"
		_sensor.append([obj.getName()+"_TOUCH","Timer_"+obj.getName()])
		alfa=100.0
		if(isCubeIcon(obj)==1):
			alfa=0
		print "<Shape>"
		_treeLevel+=1
		writeAppearanceNode(node,_treeLevel)
		_treeLevel-=1
#		print "<Appearance>\n<Material DEF= \""+obj.getName()+"_MAT\" transparency=\"%.3f\"/></Appearance><Box size=\"%.3f %.3f %.3f\"/>"%(alfa,obj.SizeX,obj.SizeY,obj.SizeZ)
		print "<Box size=\"1.0 1.0 1.0\"/></Shape>"
		print "</Transform>"
		#####################################################################
	if(isCubeIcon(obj)!=1):
		if (obj.getData()):
			for i in range(_treeLevel):
				print "	",
			print "<Shape>"
			_treeLevel+=1
			if(hasMaterial(obj)==1):
				writeAppearanceNode(node,_treeLevel)
			writeGeometryNode(node,_treeLevel)
			_treeLevel-=1
			for i in range(_treeLevel):
				print "	",
			print "</Shape>"
		if hasChilds(obj):
			writeX3D(node[1],_treeLevel)
		_treeLevel-=1
		for i in range(_treeLevel):
			print "	",
	print "</Transform>"
	
def writeX3DMesh(obj,_treeLevel):
	DrawProgressBar(0.0, " Escreve Malha (entidade)")  
	writeTransformNode(obj,_treeLevel)

def imprimeCabecalho():
	DrawProgressBar(0.0, " Cabecalho X3D")  
	print "	<head>"
	print "		<meta name=\"filename\" content=\"",
	print Blender.sys.basename(filename),
	print"\"/>"
	print "		<meta name=\"description\" content=\"Criado e/ou editado com Blender Ed. 2.35 ou superior\"/>"
	print "		<meta name=\"author\" content=\"Rodrigo de Godoy Domingues (Spy)\"/>"
	print "		<meta name=\"e-mail\" content=\"spy@lsi.usp.br spy@opengl.com.br\"/>"
	print "		<meta name=\"created\" content=\"",
	print Blender.sys.time(),
	print "\"/>"
	print "		<meta name=\"copyright\" content=\"CopyLeft Hiperespaco Logicware Consultoria Ltda\"/>"
	print "		<meta name=\"generator\" content=\"Blender Exporter-Framework-X3D\"/>"
	print "	</head>"

def writeLightData(obj):
	DrawProgressBar(0.0, obj.getName()+" Escreve Dado de Iluminacao")  
	loc=obj.loc
	intensity=obj.getData().energy
	ambInt=obj.getData().getHaloInt()
	cor=obj.getData().col
	
	if obj.getType()==1: #PointLight
		print "		<PointLight DEF=\""+obj.getName()+"\" intensity=\"%.3f\" color=\"%.3f %.3f %.3f\" location=\"%.3f %.3f %.3f\"/>"%(intensity,cor[0],cor[1],cor[2],loc[0],loc[1],loc[2])
	elif obj.getType()==2: #SpotLight
		beamwidth=obj.getData().bias
		raio=obj.getData().dist
		direc=obj.rot
		angulo=obj.getData().spotSize
		print "		<SpotLight DEF=\""+obj.getName()+"\" intensity=\"%.3f\" color=\"%.3f %.3f %.3f\" location=\"%.3f %.3f %.3f\" direction=\"%.3f %.3f %.3f\" beamWidth=\"%.3f\" cutOffAngle=\"%.3f\" radius=\"%.3f\"/>"%(intensity,cor[0],cor[1],cor[2],loc[0],loc[1],loc[2],direc[0],direc[1],direc[2],beamwidth,angulo,raio)
		
def writeCamData(obj):
	DrawProgressBar(0.0, obj.getName()+" Escreve Dado de Camera")  
	loc=obj.loc
	ori=euler2AxisAngle(obj.rot)
	nome=obj.getName()
	print "		<Viewpoint DEF=\""+nome+"\" position=\"%.3f %.3f %.3f\" orientation=\"%.3f %.3f %.3f %.3f\" descriprion=\"Camera Da Cena\"/>"%(loc[0],loc[1],loc[2],ori[0],ori[1],ori[2],ori[3])
	
def writeX3D(arv,_treeLevel):
	DrawProgressBar(0.0, "Escreve Entidades Graficas X3D")  
	for obj in arv:
		tipo=type(obj[0].getData())
		if (tipo==Types.NMeshType) or (not obj[0].getData()):
			writeX3DMesh(obj,_treeLevel)
		elif tipo==Types.LampType:
			writeLightData(obj[0])
		elif tipo==Types.CameraType:
			writeCamData(obj[0])
		if obj[1]:
#			writeX3D(obj[1])
			if hasChilds(obj):
				_treeLevel+=1
				writeX3D(obj[1],_treeLevel)
				_treeLevel-=1

def writeSensorData(obj):
	DrawProgressBar(0.0, obj.getName()+" Escreve TimeSensorData")  
	timername="Timer_"+obj.getName()
	print "<!-- ########################################################## -->"
	print "<TimeSensor DEF=\"Timer_"+obj.getName()+"\" loop=\"false\" cycleInterval=\"20.0\"/>"
	_objtimer.append([obj,timername])
	nome=obj.getName()
	interpData=getSkipData(obj,_x3dInterpolators)
	for k in interpData[1]:
		print "<!-- ############################################################## -->"
		print "<ROUTE fromNode=\""+timername+"\" fromField=\"fraction_changed\"",
		if k[0]=="PositionInterpolator":
			print " toNode=\""+nome+"_PosInterp\" toField=\"set_fraction\"/>"
			print "<ROUTE fromNode=\""+nome+"_PosInterp\" fromField=\"value_changed\" toNode=\""+nome+"_OBJ\" toField=\"set_translation\"/>"
		elif k[0]=="OrientationInterpolator":
			print "toNode=\""+nome+"_RotInterp\" toField=\"set_fraction\"/>"
			print "<ROUTE fromNode=\""+nome+"_RotInterp\" fromField=\"value_changed\" toNode=\""+nome+"_OBJ\" toField=\"set_rotation\"/>"
		elif k[0]=="DeltaPositionInterpolator":
			print "toNode=\""+nome+"_DPosInterp\" toField=\"set_fraction\"/>"
			print "<ROUTE fromNode=\""+nome+"_DPosInterp\" fromField=\"value_changed\" toNode=\""+nome+"_OBJ\" toField=\"set_translation\"/>"
	print
	print "<!-- ############################################################## -->"
	print
	

def writeRouteData(obj):
	DrawProgressBar(0.0, obj.getName()+" writeRouteData")  
	nome=obj.getName()
	filhos=findchilds(obj)
	acoes=[]
	if filhos:
		for acao in filhos:
			if hasAction(acao):
				acoes.append(acao)
		for route in acoes:
			fromNode=route.getParent().getName()+"_TOUCH"
			fromField=""
			toNode=""
			toField=""
			pp=route.getAllProperties()
			for p in pp:
				if p.name=="fromField":
					fromField=p.getData()
				if p.name=="toNode":
					toNode=p.getData()
				if p.name=="toField":
					toField=p.getData()
			print "<ROUTE fromNode=\""+fromNode+"\" fromField=\""+fromField+"\" toNode=\""+toNode+"\" toField=\""+toField+"\"/>"

def writeVisibilitySensors(obj):
	print "<!-- ####################################################################"
	print "					Regras para Visibilidade			"
	print "############################################################ -->"
	print "<TimeSensor DEF=\""+obj+"_TInv\" loop=\"false\" cycleInterval=\"0.5\"/>"
	print "<TimeSensor DEF=\""+obj+"_TVis\" loop=\"false\" cycleInterval=\"0.5\"/>"
	print "<ROUTE fromNode=\""+obj+"_TInv\" fromField=\"fraction_changed\" toNode=\""+obj+"_Inv\" toField=\"set_fraction\"/>"
	print "<ROUTE fromNode=\""+obj+"_Inv\" fromField=\"value_changed\" toNode=\""+obj+"_MAT\" toField=\"transparency\"/>"
	print "<ROUTE fromNode=\""+obj+"_TVis\" fromField=\"fraction_changed\" toNode=\""+obj+"_Vis\" toField=\"set_fraction\"/>"
	print "<ROUTE fromNode=\""+obj+"_Vis\" fromField=\"value_changed\" toNode=\""+obj+"_MAT\" toField=\"transparency\"/>"

			
def writeAnimRouteData(arv):
	for node in __visibleTimer:
		writeVisibilitySensors(node)
	for node in __sensors:
#constrói os sensores de tempo e os routes dos sensores de
#tempo para os interpoladores
			writeSensorData(node)
#Constrói os routes para os objetos de ação usando objetos
#empty filhos dos mesmos
	for node in __actions:
			print "<!-- ###################Acao de Objeto########################### -->"
			writeRouteData(node)

def distancia(p1,p2):
	return sqrt((p1[0]-p2[0])*(p1[0]-p2[0])+(p1[1]-p2[1])*(p1[1]-p2[1])+(p1[2]-p2[2])*(p1[2]-p2[2]))
			
def getScale(obj):
	c=obj.getBoundBox()
	ex=distancia(c[0],c[4])
	ey=distancia(c[2],c[1])
	ez=distancia(c[1],c[0])
	return [ex,ey,ez]

def getSize(obj):
	c=obj.getBoundBox()
	ex=0
	ey=0
	ez=0
	if c[0][0]>c[4][0]:
		ex=c[0][0]-c[4][0]
	else:
		ex=c[4][0]-c[0][0]
	if c[2][1]>c[1][1]:
		ey=c[2][1]-c[1][1]
	else:
		ey=c[1][1]-c[2][1]
	if c[1][2]>c[0][2]:
		ez=c[1][2]-c[0][2]
	else:
		ez=c[0][2]>c[1][2]
	return [ex,ey,ex]
	
def writeCubeSensor(node,_treeLevel):
	obj=node[0]
	DrawProgressBar(0.0, obj.getName()+" writeCubeSensor")  
	transf=getSkipData(obj,_objtransform)
	print "<Transform DEF=\""+obj.getName()+"_CUBE\" translation=\"%.3f %.3f %.3f\" scale=\"%.3f %.3f %.3f\" rotation=\"%.3f %.3f %.3f %.3f\"> "%(transf[1][1][0],transf[1][1][1],transf[1][1][2],transf[1][2][0],transf[1][2][1], transf[1][2][2], transf[1][0][0],transf[1][0][1],transf[1][0][2],transf[1][0][3])
	if hasAnimation(obj)==1:
		escala=getSize(obj)
		print "<TouchSensor DEF=\""+obj.getName()+"_TOUCH\"/>"
		_sensor.append([obj.getName()+"_TOUCH","Timer_"+obj.getName()])
		print "<Shape>\n <Appearance>\n<Material transparency=\"100.0\"/></Appearance><Box size=\"%.3f %.3f %.3f\"/></Shape>"%(escala[0],escala[1],escala[2])
	if node[1]:
		writeTouchSensorData(node[1],_treeLevel+1)
	print "</Transform>"

def writeTouchSensorData(nodes,_treeLevel):
	DrawProgressBar(0.0, " writeTouchSensor")  
	for node in nodes:
		if type(node[0].getData())==Types.NMeshType:
			writeCubeSensor(node,_treeLevel)

def writeTouchRouteData():
	DrawProgressBar(0.0, "WriteTouchRoute")  
	for k in _sensor:
		print "<ROUTE fromNode=\""+k[0]+"\" fromField=\"touchTime\" toNode=\""+k[1]+"\" toField=\"startTime\"/>"

def initX3D(arv):
	DrawProgressBar(0.0, "Inicia Escrita de Dados X3D")  
	_treeLevel=2
	print "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
	print "<!DOCTYPE X3D PUBLIC \"ISO//Web3D//DTD X3D 3.0//EN\"   \"http://www.web3d.org/specifications/x3d-3.0.dtd\">"
	print "<X3D profile=\"Full\">"
	imprimeCabecalho()
	print "	<Scene>"
	writeX3D(arv,_treeLevel)
	#writeTouchSensorData(arv,_treeLevel)
	writeAnimRouteData(arv)
#	writeTouchRouteData()
	print "	</Scene>"
	print "</X3D>"
	DrawProgressBar(0.0, "Fim de Escrita de dados X3D")  
####################################################################
########### Rotina para imprimir a hierarquia da ï¿½vore
####################################################################
def treeinfo(tree,level):
	if level==0:
		print "Raï¿½es da ï¿½vore:"
	for i in range(level):
		print "	",
	print "[",
	for k in tree:
		print k[0].getName(),
		print " ",
	print "]"
	for k in tree:
		for i in range(level):
			print "	",
		print "filhos de: ",
		print k[0].getName()
		treeinfo(k[1],level+1)

####################################################################
############ Busca os dados em uma SkipList
############ Retorno: [obj,dado]
####################################################################
def getSkipData(obj,skip):
	for o in skip:
		if o:
			if o[0]==obj:
				return o
	return None

####################################################################
########## Rotina Principal
####################################################################
obs=Blender.Object.Get()
#print "As relacoes sao: "
#print buildrelations()
arv=buildtree()
#treeinfo(arv,0)
imparv(arv,0)
initX3D(arv)