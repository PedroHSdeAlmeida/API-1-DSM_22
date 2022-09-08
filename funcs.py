from importlib.metadata import requires
from flask import Flask, render_template,request, url_for, redirect, session
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = 'super secret key'

mysql = MySQL(app)

def SlcMySQL(TabelaBd,CampoBd,CampoFm):
    x=0
    cursor = mysql.connection.cursor()
    textoSQL = f' SELECT * FROM {TabelaBd} WHERE '
    for values in CampoBd:
        if x==0:
            textoSQL+= f'{CampoBd[x]} = {CampoFm[x]} '
        else:
            textoSQL+= f' and {CampoBd[x]} = {CampoFm[x]}'
        x+=1
    cursor.execute(textoSQL)
    resultado = cursor.fetchone()
    mysql.connection.commit()
    cursor.close()
    return resultado

def InsMySQL(TabelaBd,CampoBd,CampoFm):
    x=0
    ValuesBD = '('
    ValuesFm = '('
    cursor = mysql.connection.cursor()
    textoSQL = f' INSERT INTO {TabelaBd} '
    for values in CampoBd:
        if values == CampoBd[-1]:
            ValuesBD += f'{CampoBd[x]})'
            ValuesFm += f'{CampoFm[x]})'
        else:
            ValuesBD += f'{CampoBd[x]},'
            ValuesFm += f'{CampoFm[x]},'  
        x+=1
    textoSQL += f' {ValuesBD} VALUES{ValuesFm}' 
    cursor.execute(textoSQL)
    mysql.connection.commit()
    cursor.close()