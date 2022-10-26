from logging import raiseExceptions
import math
import os
from email.message import EmailMessage
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ssl
import smtplib
from importlib.metadata import requires
from reportlab.pdfgen import canvas
from flask import Flask, render_template,request, url_for, redirect, session, abort
from flask_mysqldb import MySQL
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'super secret key'

mysql = MySQL(app)

def SlcMySQL(TabelaBd,CampoBd,CampoFm):
    x=0
    cursor = mysql.connection.cursor()
    textoSQL = f' SELECT * FROM {TabelaBd} where'
    for values in CampoBd:
        if x==0:
            textoSQL+= f' {CampoBd[x]} = "{CampoFm[x]}" '
        else:
            textoSQL+= f' and {CampoBd[x]} = "{CampoFm[x]}"'
        x+=1

    cursor.execute(textoSQL)
    resultado = cursor.fetchall()
    mysql.connection.commit()
    cursor.close()
    return resultado

def SlcEspecificoMySQL(TabelaBd,CampoBd,CampoFm, CampoEs):
    x=0
    y=0
    cursor = mysql.connection.cursor()
    textoSQL = ''
    for values in CampoEs:
        if y==0:
            textoSQL += f'SELECT {CampoEs[y]}'
        else:
            textoSQL += f', {CampoEs[y]}'
        y+=1
    textoSQL += f' FROM {TabelaBd}'
    for values in CampoBd:
        if x==0:
            textoSQL+= f' WHERE {CampoBd[x]} = "{CampoFm[x]}" '
        else:
            textoSQL+= f' and {CampoBd[x]} = "{CampoFm[x]}"'
        x+=1
    cursor.execute(textoSQL)
    resultado = cursor.fetchall()
    mysql.connection.commit()
    cursor.close()
    return resultado

def SlcEspecificoComORMySQL(TabelaBd,CampoBd,CampoFm, CampoEs,CampoWrAO):
    x=0
    y=0
    cursor = mysql.connection.cursor()
    textoSQL = ''
    for values in CampoEs:
        if y==0:
            textoSQL += f'SELECT {CampoEs[y]}'
        else:
            textoSQL += f', {CampoEs[y]}'
        y+=1
    textoSQL += f' FROM {TabelaBd}'
    for values in CampoBd:
        if CampoWrAO[x] == 0:
            if x==0:
                textoSQL+= f' WHERE {CampoBd[x]} = "{CampoFm[x]}" '
            else:
                if CampoWrAO[x+1] == 0:
                    textoSQL+= f' and {CampoBd[x]} = "{CampoFm[x]}"'
                else:
                    textoSQL+= f' and ({CampoBd[x]} = "{CampoFm[x]}"'
        else:
            if x==0:
                textoSQL+= f' WHERE {CampoBd[x]} = "{CampoFm[x]}" '
            else:
                textoSQL+= f' or {CampoBd[x]} = "{CampoFm[x]}")'
        x+=1
    cursor.execute(textoSQL)
    resultado = cursor.fetchall()
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
            ValuesFm += f'"{CampoFm[x]}")'
        else:
            ValuesBD += f'{CampoBd[x]},'
            ValuesFm += f'"{CampoFm[x]}",'
        x+=1
    textoSQL += f' {ValuesBD} VALUES{ValuesFm}'
    cursor.execute(textoSQL)
    mysql.connection.commit()
    cursor.close()

def upMySQL(TabelaBd,CampoBd,CampoFm,CampoWr,CampoPs):
    x=0
    y=0
    cursor = mysql.connection.cursor()
    textoSQL = f' UPDATE {TabelaBd} SET '
    for values in CampoBd:
        if x == 0:
            textoSQL += f'{CampoBd[x]} = "{CampoFm[x]}" '
        else:
            textoSQL += f', {CampoBd[x]} = "{CampoFm[x]}" '
        x+=1

    for values in CampoWr:
        if y == 0:
            textoSQL += f'WHERE {CampoWr[y]} = "{CampoPs[y]}"'
        else:
            textoSQL += f'AND {CampoWr[y]} = "{CampoPs[y]}"'
        y+=1

    cursor.execute(textoSQL)
    mysql.connection.commit()
    cursor.close()

def DelMySQL(TabelaBd,CampoBd,CampoFm):
    x=0
    cursor = mysql.connection.cursor()
    textoSQL = f' DELETE FROM {TabelaBd} WHERE '
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


def geraId(nome, agencia, cpf):
    #O id é gerado a partir de alguns processos de criptografia
    #os primeiros 4 digitos são gerados a partir do id da agência
    #os próximos 4 digitos são valores randomicos do cpf do usuario
    #os próximos 4 digitos são valores criptografados a partir do nome do usuario
    alfabetoCript = ['e', 'd', 'n', 'z', 'w', 'f', 't', 'u', 'p', 'o', 's', 'v', 'y', 'r', 'j', 'x', 'i', 'a', 'm', 'b', 'q', 'c', 'g', 'h', 'k', 'l']
    nome = nome.lower()
    arr_nome = nome.split(" ")
    letra_prim_nome = arr_nome[0][0:1]
    letra_seg_nome = ''
    if len(arr_nome)<1:
        letra_seg_nome = arr_nome[1][0:1]
    format_agencia = ""
    arr_cpf = []
    cont_caractere = 0

    #completa com zeros a esquerda caso a agência tenha menos que 4 caracteres no id
    if len(agencia) < 4:
        qt_zeros = 4 - len(agencia)
        while qt_zeros != 0:
            format_agencia += '0'
            qt_zeros -= 1
        format_agencia += agencia
        agencia = format_agencia

    nummeroConta = agencia

    #gerando um array com os valores splitados
    for num in cpf:
        arr_cpf.append(num)

    #gerando e adicionando 4 valores random a string idUsuario
    while cont_caractere < 4:
        #gerar valor aleatorio 4 vezes dentro do limite do array (lenght)
        random_index = random.randint(0, len(arr_cpf)-1)
        nummeroConta += arr_cpf [random_index]
        cont_caractere += 1

    nummeroConta += str(alfabetoCript.index(letra_prim_nome))
    if letra_seg_nome:
        nummeroConta += str(alfabetoCript.index(letra_seg_nome))

    #caso não some 12 caracteres esse while concatena zeros ao final da string
    while len(nummeroConta)<12:
        nummeroConta += '0'

    return nummeroConta

def TirarPontoeTraco(CPF):
    CPF = CPF.replace(".","")
    CPF = CPF.replace("-","")
    return CPF

def Transacao(conta_origem, conta_destino, tipo, valor, status):
    data = datetime.now()
    InsMySQL('tb_transacao',
            CampoBd = ['id_conta_origem','id_conta_destino','Datatime','tipo','valor', 'status_transacao'],
            CampoFm = [conta_origem, conta_destino, data, tipo, valor, status])

def email(conta_origem, tipo, valor):
    data = datetime.now()
    id_ultima_movimentacao = SlcEspecificoMySQL(TabelaBd='tb_transacao',
                                                CampoBd=['id_conta_origem'],
                                                CampoFm=[conta_origem],
                                                CampoEs=['max(id_transacao)'])

    dados_transacao = SlcEspecificoMySQL(TabelaBd='tb_transacao',
                                        CampoBd=['id_transacao'],
                                        CampoFm=[id_ultima_movimentacao[0][0]],
                                        CampoEs=['*'])
    
    nome_origem = SlcEspecificoMySQL (TabelaBd='tb_contabancaria INNER JOIN tb_usuario ON tb_contabancaria.id_usuario = tb_usuario.id_usuario',
                                            CampoBd=['id_conta'],
                                            CampoFm=[dados_transacao[0][1]],
                                            CampoEs=['tb_usuario.nome'])

    nome_destino = SlcEspecificoMySQL (TabelaBd='tb_contabancaria INNER JOIN tb_usuario ON tb_contabancaria.id_usuario = tb_usuario.id_usuario',
                                            CampoBd=['id_conta'],
                                            CampoFm=[dados_transacao[0][2]],
                                            CampoEs=['tb_usuario.nome'])
    
    numero_conta_origem = SlcEspecificoMySQL(TabelaBd='tb_contabancaria',
                                            CampoBd=['id_conta'],
                                            CampoFm=[dados_transacao[0][1]],
                                            CampoEs=['numeroconta'])
    
    numero_conta_destino = SlcEspecificoMySQL(TabelaBd='tb_contabancaria',
                                            CampoBd=['id_conta'],
                                            CampoFm=[dados_transacao[0][2]],
                                            CampoEs=['numeroconta'])

    movimentacao = {
        'conta_origem' : numero_conta_origem[0][0],
        'nome_origem' : nome_origem[0][0],
        'conta_destino' : numero_conta_destino[0][0],
        'nome_destino' : nome_destino[0][0],
        'tipo' : tipo,
        'data': str(data.strftime('%x')),
        'hora': str(data.strftime('%X')),
        'id' : id_ultima_movimentacao[0][0],
        'valor' : valor
    }

    email = SlcEspecificoMySQL (TabelaBd='tb_contabancaria INNER JOIN tb_usuario ON tb_contabancaria.id_usuario = tb_usuario.id_usuario',
                                            CampoBd=['id_conta'],
                                            CampoFm=[dados_transacao[0][1]],
                                            CampoEs=['tb_usuario.email'])

    nome_comp = criaComprovante(movimentacao, numero_conta_origem[0][0])

    emailComprovante(nome_comp, email[0][0])

    os.remove(nome_comp)

    if movimentacao['tipo'] == 'transferencia':
        email = SlcEspecificoMySQL (TabelaBd='tb_contabancaria INNER JOIN tb_usuario ON tb_contabancaria.id_usuario = tb_usuario.id_usuario',
                                                CampoBd=['id_conta'],
                                                CampoFm=[dados_transacao[0][2]],
                                                CampoEs=['tb_usuario.email'])

        nome_comp = criaComprovante(movimentacao, numero_conta_destino[0][0])

        emailComprovante(nome_comp, email[0][0])

        os.remove(nome_comp)

def criaComprovante (dicionario, numero_conta):
    nome_comp = f"{dicionario['id']}{numero_conta}.pdf"
    c = canvas.Canvas(nome_comp)
    c.setFont("Helvetica", 12)
    if dicionario ['tipo'] == 'Depósito':
        c.drawString(80,750,"Py.NK Internet Banking")
        c.drawString(80,720,"Comprovante de Depósito")
        c.drawString(80,690,f"+R${dicionario['valor']} depositado.")
        c.line(80,675,510,675)
        c.drawString(80,650,f"Data do Depósito: {dicionario['data'][3:5]}/{dicionario['data'][:2]}/{dicionario['data'][6:]}")
        c.drawString(80,620,f"Horário do Depósito: {dicionario['hora']}")
        c.drawString(80,590,f"ID da Transação: {dicionario['id']}")
    elif dicionario ['tipo'] == 'Saque':
        c.drawString(80,750,"Py.NK Internet Banking")
        c.drawString(80,720,"Comprovante de Saque")
        c.drawString(80,690,f"-R${dicionario['valor']} sacado.")
        c.line(80,675,510,675)
        c.drawString(80,650,f"Data do Saque: {dicionario['data'][3:5]}/{dicionario['data'][:2]}/{dicionario['data'][6:]}")
        c.drawString(80,620,f"Horário do Saque: {dicionario['hora']}")
        c.drawString(80,590,f"ID da Transação: {dicionario['id']}")
    elif dicionario['tipo'] == 'transferencia':
        if numero_conta == dicionario['conta_origem']:
            c.drawString(80,750,"Py.NK Internet Banking")
            c.drawString(80,720,f"Comprovante de Transferência Realizada")
            c.drawString(80,690,f"R${dicionario['valor']} transferido para {dicionario['nome_destino']}")
            c.line(80,675,510,675)
            c.drawString(80,650,f"Data da Transferência: {dicionario['data'][3:5]}/{dicionario['data'][:2]}/{dicionario['data'][6:]}")
            c.drawString(80,620,f"Horário da Transferência: {dicionario['hora']}")
            c.drawString(80,590,f"Enviado para: {dicionario['nome_destino']}")
            c.drawString(80,560,f"Numero de conta: {dicionario['conta_destino']}")
            c.drawString(80,530,f"ID da Transação: {dicionario['id']}")
        elif numero_conta == dicionario['conta_destino']:
            c.drawString(80,750,"Py.NK Internet Banking")
            c.drawString(80,720,f"Comprovante de Transferência Recebida")
            c.drawString(80,690,f"R${dicionario['valor']} recebido de {dicionario['nome_origem']}")
            c.line(80,675,510,675)
            c.drawString(80,650,f"Data da Transferência: {dicionario['data'][3:5]}/{dicionario['data'][:2]}/{dicionario['data'][6:]}")
            c.drawString(80,620,f"Horário da Transferência: {dicionario['hora']}")
            c.drawString(80,590,f"Enviado por: {dicionario['nome_origem']}")
            c.drawString(80,560,f"Numero de conta: {dicionario['conta_origem']}")
            c.drawString(80,530,f"ID da Transação: {dicionario['id']}")
    c.showPage()
    c.save()
    return nome_comp 

def LoadConfig():
    config = {}
    conf = open("config.conf", "r")
    for line in conf:
        line = line.strip()
        if line[:4] == 'host':
            config['host'] = line[7:]
        elif line[:4] == 'port':
            config['port'] = int(line[6:])
        elif line[:4] == 'user':
            config['user'] = line[7:]
        elif line[:8] == 'password':
            config['password'] = line[11:]
        elif line[:2] == 'db':
            config['db'] = line[5:]
    conf.close()
    return config

def cancelMySQL(id_usuario, senha, numeroconta):
    pesquisa = SlcEspecificoMySQL(TabelaBd='tb_contabancaria INNER JOIN tb_usuario ON tb_contabancaria.id_usuario = tb_usuario.id_usuario',
                               CampoBd=['tb_usuario.id_usuario', 'tb_contabancaria.numeroconta'],
                               CampoFm=[id_usuario, numeroconta], 
                               CampoEs=['saldo', 'tb_usuario.senha'])
    saldo = pesquisa[0][0]
    senhaUsuario = pesquisa[0][1]
    if senha == senhaUsuario:
        if saldo > 0: 
            raise Exception('601')
        elif saldo < 0:
            raise Exception('602')
        else:
            upMySQL(TabelaBd='tb_contabancaria',
                CampoBd=['status_contabancaria'],
                CampoFm=[2],
                CampoWr=['id_usuario', 'numeroconta'],
                CampoPs=[id_usuario, numeroconta])
            raise Exception('603')

    else:
        raise Exception('401')

def emailCadastro(id, destinatario, aceite):
    remetente = "py.nk.fatec@gmail.com"
    senha = "hjdixtkskjwtvxqr"
    if aceite == True:
        numeroconta = SlcEspecificoMySQL('tb_contabancaria',
                                         CampoBd=['id_conta'],
                                         CampoFm=[id],
                                         CampoEs=['numeroconta'])
        
        assunto = 'Bem vindo ao Py.NK!'
        corpo = f'''Seja bem vindo(a)! 
        Nós do PyNK agradecemos a preferência, utilize o código {str(numeroconta)[3:-5]} para acessar sua conta.'''

    elif aceite == False:
        assunto = 'Irregularidade no cadastro Py.NK.'
        corpo = f'''Olá, algo de errado aconteceu.
        Durante a triagem do seu cadastro o Py.NK encontrou algumas divergências, sua conta não foi criada.'''

    em = EmailMessage()
    em['From'] = remetente
    em['To'] = destinatario
    em['subject'] = assunto
    em.set_content(corpo)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(remetente, senha)
        smtp.sendmail(remetente, destinatario, em.as_string())


def periodoEntreDatas(data1, data2):
    data1 = datetime.strptime(data1, "%Y-%m-%d")
    data2 = datetime.strptime(data2, "%Y-%m-%d")
    return abs((data2 - data1).days)

def emailComprovante(nome_arq, destinatario):
    subject = "Comprovante de movimentação"
    body = "Aqui está o comprovante da sua última movimentação."
    sender_email = "py.nk.fatec@gmail.com"
    receiver_email = destinatario
    password = "hjdixtkskjwtvxqr"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    filename = nome_arq  

    with open(filename, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
  
    encoders.encode_base64(part)

    part.add_header(
        "Content-Disposition",
        f"attachment; filename={filename}"
    )

    message.attach(part)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
        smtp.login(sender_email, password)
        smtp.sendmail(sender_email, receiver_email, message.as_string())
     
erro = {'400': 'O servidor não entendeu a requisição pois está com uma sintaxe inválida.',
'401': 'Antes de fazer essa requisição se autentifique. Credenciais inválidas.',
'404': 'Página não encontrada.',
'403': 'Acesso restrito.',
'500': 'Erro interno do servidor.',
'503': 'Serviço indisponível.',
'504': 'Gateway timeout',
'601' : 'Você ainda possui saldo em conta, realize o saque e depois prossiga com o cancelamento',
'602' : 'Você ainda possui pendências  com o banco, regularize sua situação antes de prosseguir com o cancelamento',
'603' : 'Você cancelou a sua conta com sucesso.'}

def calculaChequeEspecial(valorDevido, tempo, porecentagem):
    valor = ((1+porecentagem)**tempo)*valorDevido
    valorTruncado = truncar(numero=valor,casaDecimal=3)
    return valorFormatadado

def truncar(numero, casaDecimal):
   sp = str(numero).split('.')
   return '.'.join([sp[0], sp[:casaDecimal]])

def ValEmReal(valor):
    valor = f"{valor:.2f}".replace(".",",")
    return valor