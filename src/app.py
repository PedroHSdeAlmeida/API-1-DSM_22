import os
import email
from email.message import EmailMessage
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date, datetime
from tokenize import Double
from flask import Flask, render_template,request, url_for, redirect, session, flash, abort
from flask_mysqldb import MySQL
import funcs
import random

config = funcs.LoadConfig()

app = Flask(__name__)
app.secret_key = 'super secret key'
# Conexão ao banco de dados
app.config['MYSQL_HOST'] = config['host']
app.config['MYSQL_PORT'] = config['port'] #Caso a porta seja a padrão, comentar linha.
app.config['MYSQL_USER'] = config['user']
app.config['MYSQL_PASSWORD'] = config['password']
app.config['MYSQL_DB'] = config['db']

mysql = MySQL(app)
# Bloco de Paginas.

#Pagina inicial
@app.route("/")
def index():
    session['login'] = False
    session['nome']  = None
    session['conta'] = None
    session['tipo']  = None
    return render_template('login.html')
#------------------------------

#Pagina Home
@app.route("/home", methods = ['POST', 'GET'])
def home():
    if session['login'] == False:
        abort(401)
    else:
        saldo = None
        if session['tipo'] == 1:
            cabecalho = ('Tipo', 'Valor','Data e hora', 'De:', 'Para:')
            saldo = funcs.ValEmReal(session['saldo'])
            VarContador=0
            
            pesquisaSQL = funcs.SlcEspecificoComORMySQL(TabelaBd='tb_transacao',
                                            CampoEs=['tipo','valor','Datatime'],
                                            CampoBd=['status_transacao','id_conta_origem','id_conta_destino'],
                                            CampoFm=[1,session['idContaBK'],session['idContaBK']],
                                            CampoWrAO=[0,0,1])
            
            pesquisaContas = funcs.SlcEspecificoComORMySQL(TabelaBd='tb_transacao',
                                            CampoEs=['id_conta_origem', 'id_conta_destino'],
                                            CampoBd=['status_transacao','id_conta_origem','id_conta_destino'],
                                            CampoFm=[1,session['idContaBK'],session['idContaBK']],
                                            CampoWrAO=[0,0,1])
            
            pesquisaSQL = [list(row) for row in pesquisaSQL]
            for row in pesquisaContas:
                
                nomes1 = funcs.SlcEspecificoMySQL('tb_contabancaria inner join tb_usuario ON  tb_usuario.id_usuario = tb_contabancaria.id_usuario',
                                                        CampoBd=['tb_contabancaria.id_conta'],
                                                        CampoFm=[row[0]],
                                                        CampoEs=['nome'])
                nomes1 = [list(row) for row in nomes1]
                                            
                nomes2 = funcs.SlcEspecificoMySQL('tb_contabancaria inner join tb_usuario ON  tb_usuario.id_usuario = tb_contabancaria.id_usuario',
                                                        CampoBd=['tb_contabancaria.id_conta'],
                                                        CampoFm=[row[1]],
                                                        CampoEs=['nome'])
                
                nomes2 = [list(row) for row in nomes2]
                
                pesquisaSQL[VarContador].append(nomes1[0][0])
                pesquisaSQL[VarContador].append(nomes2[0][0])
                pesquisaSQL[VarContador][1] = funcs.ValEmReal(pesquisaSQL[VarContador][1])
                VarContador+=1
                
            return render_template('homenew.html',saldo=saldo,cabecalhoTabela=cabecalho,pesquisaSQLTabela=pesquisaSQL)
        else:
            saldo = f"{session['saldo']:.2f}".replace(".",",")
            return render_template('homeG.html',saldo=saldo)
#------------------------------

#Aplicar filtro no extrato
@app.route("/FiltroExtrato",  methods = ['POST', 'GET'])
def FiltroExtrato():
    if request.method == "POST":
        cabecalho   = ('Tipo', 'Valor','Data e hora', 'De:', 'Para:')
        saldo       = funcs.ValEmReal(session['saldo'])
        VarContador = 0
        DataDe      = request.form['DataExtratoDe']
        DateAte     = request.form['DataExtratoAte']
        cursor = mysql.connection.cursor()
        
        textoSQL = f"""SELECT tipo, valor, Datatime FROM tb_transacao 
        WHERE status_transacao = "1" and Datatime >= '{DataDe} 00:00:00' and Datatime < '{DateAte} 23:59:59' 
        and ( id_conta_origem = "{session['idContaBK']}"or id_conta_destino = "{session['idContaBK']}")"""
        
        cursor.execute(textoSQL)
        pesquisaSQL = cursor.fetchall()
        mysql.connection.commit()     
        
        textoSQL2 = f"""SELECT id_conta_origem, id_conta_destino FROM tb_transacao 
        WHERE status_transacao = "1" and Datatime >= '{DataDe} 00:00:00' and Datatime < '{DateAte} 23:59:59'
        and ( id_conta_origem = "{session['idContaBK']}" or id_conta_destino = "{session['idContaBK']}" )"""
        
        cursor.execute(textoSQL2)
        pesquisaContas = cursor.fetchall()
        mysql.connection.commit()  
        
        
        cursor.close()   
            
        pesquisaSQL = [list(row) for row in pesquisaSQL]
        for row in pesquisaContas:
            nomes1 = funcs.SlcEspecificoMySQL('tb_contabancaria inner join tb_usuario ON  tb_usuario.id_usuario = tb_contabancaria.id_usuario',
                                                        CampoBd=['tb_contabancaria.id_conta'],
                                                        CampoFm=[row[0]],
                                                        CampoEs=['nome'])  
            nomes2 = funcs.SlcEspecificoMySQL('tb_contabancaria inner join tb_usuario ON  tb_usuario.id_usuario = tb_contabancaria.id_usuario',
                                                        CampoBd=['tb_contabancaria.id_conta'],
                                                        CampoFm=[row[1]],
                                                        CampoEs=['nome'])
            nomes1 = [list(row) for row in nomes1]   
            nomes2 = [list(row) for row in nomes2]
                
            pesquisaSQL[VarContador].append(nomes1[0][0])
            pesquisaSQL[VarContador].append(nomes2[0][0])
            pesquisaSQL[VarContador][1] = funcs.ValEmReal(pesquisaSQL[VarContador][1])
            VarContador+=1
            
        return render_template('home.html',saldo=saldo,cabecalhoTabela=cabecalho,pesquisaSQLTabela=pesquisaSQL)
    return render_template('home.html')
#------------------------------

#Pagina Deposito
@app.route("/deposito")
def deposito():
    if session['saldo'] != None:
        saldo = f"{session['saldo']:.2f}".replace(".",",")
    return render_template('deposito.html',saldo=saldo)

#------------------------------

#Pagina Saque
@app.route("/saque")
def saque():
    saldo = f"{session['saldo']:.2f}".replace(".",",")
    return render_template('saque.html',saldo=saldo)
#------------------------------

@app.route("/SaqueConta",  methods = ['POST', 'GET'])
def SaqueConta():
    if request.method == "POST":
        valor = float(request.form['valor'])
        if valor >= 0:
            capital_total = funcs.SlcEspecificoMySQL('tb_capitaltotal',
                                                    CampoBd=['id_capitaltotal'],
                                                    CampoFm=['1'],
                                                    CampoEs=['capitalinicial'])
            if valor <= capital_total[0][0]:
                valor = float(session['saldo']) - valor
                NewCapTot = capital_total[0][0] - float(request.form['valor'])
                     
                funcs.upMySQL('tb_contabancaria',
                               CampoBd=['saldo'],
                               CampoFm=[valor],
                               CampoWr=['numeroconta'],
                               CampoPs=[session['conta']])
                
                funcs.upMySQL('tb_capitaltotal',
                               CampoBd=['capitalinicial'],
                               CampoFm=[NewCapTot],
                               CampoWr=['id_capitaltotal'],
                               CampoPs=[1])

                saldoAtualizado = funcs.SlcEspecificoMySQL('tb_contabancaria ',
                                                            CampoBd=['numeroconta'],
                                                            CampoFm=[session['conta']],
                                                            CampoEs=['saldo'])

                idConta = funcs.SlcEspecificoMySQL('tb_contabancaria',
                                                            CampoBd=['numeroconta'],
                                                            CampoFm=[session['conta']],
                                                            CampoEs=['id_conta'])
                
                if valor < 0:
                    pesquisaSQL = funcs.SlcEspecificoMySQL(TabelaBd='tb_cheque_especial',
                                                           CampoBd=['id_conta', 'ativo'],
                                                           CampoFm=[idConta[0][0], 1],
                                                           CampoEs=['valor_devido', 'data_inicio'])
                    if pesquisaSQL:
                        valorDevido = pesquisaSQL[0][0]
                        data = pesquisaSQL[0][1]

                        dataPeriodo = funcs.periodoEntreDatas(data1=str(data),data2=str(date.today()))

                        pesquisaSQLRegraCheque = funcs.SlcEspecificoMySQL(TabelaBd='tb_regra_operacoes',
                                                                          CampoBd=['id_regra_operacoes'],
                                                                          CampoFm=[1],
                                                                          CampoEs=['porcentagem', 'valor_fixo'])
                        porcentagem = pesquisaSQLRegraCheque[0][0]
                        valor_fixo = pesquisaSQLRegraCheque[0][1]
                        valorDevido = funcs.calculaChequeEspecial(tempo=dataPeriodo, porecentagem=porcentagem, valorDevido=valorDevido)
                        
                        valorDevido = valorDevido + valor
                        funcs.InsMySQL(TabelaBd='tb_cheque_especial',
                                       CampoBd=['id_conta', 'data_inicio', 'data_final', 'valor_devido', 'ativo'],
                                       CampoFm=[idConta[0][0],  datetime.now(), None, valorDevido, True])
                    else:
                        funcs.InsMySQL(TabelaBd='tb_cheque_especial',
                                       CampoBd=['id_conta', 'data_inicio', 'data_final', 'valor_devido', 'ativo'],
                                       CampoFm=[idConta[0][0],  datetime.today(), None, valor, True])

                funcs.Transacao(idConta[0][0], idConta[0][0], 'Saque', float(request.form['valor']), '1')
                funcs.email(conta_origem=idConta[0][0], tipo='Saque', valor= float(request.form['valor']))

                for row in saldoAtualizado:
                    session['saldo'] = row[0]
                return saque()
            else:
                flash ("Não é possivel realizar o saque!")
                return redirect(url_for('saque'))
        else:
            return saque()

#------------------------------
#Deposito de Conta
@app.route("/depositoConta",  methods = ['POST', 'GET'])
def depositoConta():
    if request.method == "POST":

        valor = float(request.form['valor'])
        if valor >= 0:

            valor = valor + float(session['saldo'])

            saldoAtualizado = funcs.SlcEspecificoMySQL('tb_contabancaria ',
                                                        CampoBd=['numeroconta'],
                                                        CampoFm=[session['conta']],
                                                        CampoEs=['saldo'])

            idConta = funcs.SlcEspecificoMySQL('tb_contabancaria',
                                                        CampoBd=['numeroconta'],
                                                        CampoFm=[session['conta']],
                                                        CampoEs=['id_conta'])

            funcs.Transacao(idConta[0][0], idConta[0][0], 'Depósito', float(request.form['valor']), '0')

            for row in saldoAtualizado:
                session['saldo'] = row[0]
            return deposito()
        return deposito()

#Pagina de Cadastro
@app.route("/cadastro.html", methods = ['POST', 'GET'])
def cadastro():
    if request.method == "POST":
        #Variaveis vindas do FORM vindas do cadastro.html
        nome            = request.form['name']
        cpf             = funcs.TirarPontoeTraco(request.form['cpf'])
        endereco        = request.form['endereco']
        dataNascimento  = request.form['datanasc']
        genero          = request.form['genero']
        senha           = request.form['senha']
        tipoConta       = request.form['tipoconta']
        email           = request.form['email']

        funcs.InsMySQL('tb_usuario',CampoBd=['cpf', 'nome', 'genero', 'endereco', 'senha', 'datanascimento','ativo', 'email'],
                       CampoFm=[cpf,nome,genero,endereco, senha,dataNascimento,'0', email])

        resultado = funcs.SlcEspecificoMySQL('tb_usuario', CampoBd=['cpf'], CampoFm=[cpf], CampoEs=['id_usuario'])
        for row in resultado:
            id_usuario = row[0]
        #Gera o numero da conta, usando o nome do usuário, id da agência e o cpf do usuário
        numeroCampo = funcs.geraId(str(nome),str(1),str(cpf))
        funcs.InsMySQL('tb_contabancaria',
                        CampoBd=['id_usuario', 'id_agencia', 'tipo', 'data_abertura', 'numeroconta', 'saldo', 'status_contabancaria'],
                        CampoFm=[id_usuario, 1, tipoConta, datetime.today(), numeroCampo, 0, '0'])
        flash(numeroCampo)
        return render_template('login.html')

    return render_template('cadastro.html')
#------------------------------

#Pagina de Login
@app.route("/login", methods = ['POST', 'GET'])
def login():
    if request.method == "POST":
        #login do usuário comum
        numeroconta = request.form['numeroconta']
        senha       = request.form['senha']
        resultado   = funcs.SlcMySQL('''tb_usuario
                                        INNER JOIN tb_contabancaria
                                        ON tb_contabancaria.id_usuario = tb_usuario.id_usuario ''',
                                    CampoBd=['tb_contabancaria.numeroconta','tb_usuario.senha','tb_contabancaria.status_contabancaria'],
                                    CampoFm=[numeroconta,senha,'1'])

        if resultado:
            for row in resultado:
                session['nome']     = row[1]
                session['saldo']    = row[15]
                session['idContaBK']= row[9]
            session['login'] = True
            session['conta'] = numeroconta
            session['tipo']  = 1
            return home()
        else:
            #Login de gerente geral e gerente de agência
            resultado   = funcs.SlcMySQL('''tb_usuario
                                            INNER JOIN tb_funcionario
                                            ON tb_funcionario.id_usuario = tb_usuario.id_usuario ''',
                                        CampoBd=['login','senha'],
                                        CampoFm=[numeroconta,senha])
            resultadocap = funcs.SlcMySQL('tb_capitaltotal',CampoBd=['id_capitaltotal'],CampoFm=['1'])
            if resultado:
                for row in resultado:
                    session['nome'] = row[1]
                session['login']    = True
                session['conta']    = numeroconta
                session['tipo']     = 2
                for row2 in resultadocap:
                    session['saldo']  = row2[1]
                return home()
            else:
                abort(401)
    else:
        abort(401)

#Bloco de conferência de depósito pendentes

@app.route("/ConferenciaDepositoTabela")
def ConferenciaDepositoTabela():
    if session['login'] == True:
        cabecalho = ('Nome', 'Número Conta', 'Valor', 'Data', '', '')

        pesquisaSQL = funcs.SlcEspecificoMySQL(TabelaBd='tb_transacao INNER JOIN tb_contabancaria ON tb_contabancaria.id_conta = tb_transacao.id_conta_origem AND tb_contabancaria.id_conta = tb_transacao.id_conta_destino INNER JOIN tb_usuario ON  tb_usuario.id_usuario = tb_contabancaria.id_usuario',
                                            CampoEs=['tb_transacao.id_transacao','tb_usuario.nome','tb_contabancaria.numeroconta' ,'tb_transacao.valor', 'tb_transacao.Datatime',],
                                            CampoBd=['status_transacao'],
                                            CampoFm=[0])

        return render_template("conferencia.html", cabecalhoTabela=cabecalho, pesquisaSQLTabela=pesquisaSQL)
    else:
        abort(401)

#Bloco de conferência de depósito pendentes

@app.route("/ConferenciaDeposito", methods = ['POST', 'GET'])
def ConferenciaDeposito():
    if request.method == "POST":

        botao = request.form.to_dict()

        IdTransacao =   request.form['IdTransacao']
        if botao['botao'] == 'Confirmar':

            pesquisaSQLTransacao =  funcs.SlcEspecificoMySQL(TabelaBd='tb_transacao',
                                                        CampoEs=['valor', 'id_conta_origem'],
                                                        CampoBd=['id_transacao'],
                                                        CampoFm=[IdTransacao])

            IdContaOrigem = pesquisaSQLTransacao[0][1]
            valorTransacao = float(pesquisaSQLTransacao[0][0])

            pesquisaSQLConta = funcs.SlcEspecificoMySQL(TabelaBd='tb_transacao INNER JOIN tb_contabancaria ON tb_contabancaria.id_conta = tb_transacao.id_conta_origem AND tb_contabancaria.id_conta = tb_transacao.id_conta_destino INNER JOIN tb_usuario ON  tb_usuario.id_usuario = tb_contabancaria.id_usuario',
                                                        CampoEs=['tb_contabancaria.id_conta' ,'tb_contabancaria.saldo'],
                                                        CampoBd=['id_transacao', 'tb_contabancaria.id_conta'],
                                                        CampoFm=[IdTransacao, IdContaOrigem])
            
            pesquisaTotalBanco = funcs.SlcEspecificoMySQL(TabelaBd='tb_capitaltotal',
                                                        CampoEs=['capitalinicial'],
                                                        CampoBd=['id_capitaltotal'],
                                                        CampoFm=[1])
                                            
            valorTotalBanco = float(pesquisaTotalBanco[0][0])
            saldoConta = float(pesquisaSQLConta[0][1])
            valor = valorTransacao + saldoConta

            valorTotalBanco = valor + valorTotalBanco

            funcs.upMySQL(TabelaBd='tb_transacao',
                      CampoBd=['status_transacao', 'Datatime'],
                      CampoFm=[1, datetime.today()],
                      CampoPs=[IdTransacao],
                      CampoWr=['id_transacao'])
            
            funcs.email(conta_origem=IdContaOrigem, tipo='Depósito', valor=valorTransacao)

            funcs.upMySQL('tb_contabancaria',
                          CampoBd=['saldo'],
                          CampoFm=[valor],
                          CampoWr=['id_conta'],
                          CampoPs=[IdContaOrigem])

            funcs.upMySQL(TabelaBd='tb_capitaltotal',
                          CampoBd=['capitalinicial'],
                          CampoFm=[valorTotalBanco],
                          CampoWr=['id_capitaltotal'],
                          CampoPs=[1])
            session['saldo'] = valorTotalBanco
            
            return ConferenciaDepositoTabela()
        else:
            funcs.upMySQL(TabelaBd='tb_transacao',
                      CampoBd=['status_transacao'],
                      CampoFm=[2],
                      CampoPs=[IdTransacao],
                      CampoWr=['id_transacao'])
            return ConferenciaDepositoTabela()
 

#------------------------------

#Bloco de requisição padrão

@app.route("/AceiteConta", methods = ['POST', 'GET'])
def AceiteConta():
    if request.method == "POST":

        botao = request.form.to_dict()
        IdConta = request.form['IdConta']
        
        email = ''
        email = funcs.SlcEspecificoMySQL('tb_usuario INNER JOIN tb_contabancaria ON tb_usuario.id_usuario = tb_contabancaria.id_usuario',
                                     CampoBd=['tb_contabancaria.id_conta'],
                                     CampoFm=[IdConta],
                                     CampoEs=['tb_usuario.email'])

        if botao['botao'] == 'Confirmar':
            funcs.upMySQL('tb_contabancaria',CampoBd=['status_contabancaria'],CampoFm=[1],
                                        CampoWr=['id_conta'],CampoPs=[IdConta])
            funcs.emailCadastro(IdConta, email, True)  
            return AceiteContaTabela()
        else:    
            funcs.upMySQL('tb_contabancaria',CampoBd=['status_contabancaria'],CampoFm=[2],
                                        CampoWr=['id_conta'],CampoPs=[IdConta])
            funcs.emailCadastro(IdConta, email, False)  
            return AceiteContaTabela()
       
#------------------------------

#Bloco de renderização da tela de Transação

@app.route("/Transacao")
def Transacao():
    if session['saldo'] != None:
        saldo = f"{session['saldo']:.2f}".replace(".",",")
    return render_template('transacao.html',saldo=saldo)

#------------------------------

#Bloco de transação entre contas

@app.route("/TransacaoConta",  methods = ['POST', 'GET'])
def TransacaoConta():
    if request.method == 'POST':
        if float(request.form['valor']) <= float(session['saldo']) and float(request.form['valor']) > 0:
            numeroConta = request.form['numeroConta']
            valor = float(request.form['valor'])

            pesquisaContaDestino = funcs.SlcEspecificoMySQL(TabelaBd='tb_contabancaria',
                                                CampoBd=['numeroconta'],
                                                CampoFm=[numeroConta],
                                                CampoEs=['id_conta', 'saldo'])

            pesquisaContaOrigem = funcs.SlcEspecificoMySQL(TabelaBd='tb_contabancaria',
                                                CampoBd=['numeroconta'],
                                                CampoFm=[session['conta']],
                                                CampoEs=['id_conta', 'saldo'])
                                                  
            IdContaDestino = pesquisaContaDestino[0][0]
            IdContaOrigem = pesquisaContaOrigem[0][0]

            valorContaDestino = pesquisaContaDestino[0][1]
            valorContaOrigem = pesquisaContaOrigem[0][1]

            valorContaDestino = valorContaDestino + valor
            valorContaOrigem = valorContaOrigem - valor

            if IdContaDestino == IdContaOrigem:
                return render_template('transacao.html')

            funcs.upMySQL(TabelaBd='tb_contabancaria',
                      CampoBd=['saldo'],
                      CampoFm=[valorContaOrigem],
                      CampoPs=[IdContaOrigem],
                      CampoWr=['id_conta'])

            funcs.upMySQL(TabelaBd='tb_contabancaria',
                      CampoBd=['saldo'],
                      CampoFm=[valorContaDestino],
                      CampoPs=[IdContaDestino],
                      CampoWr=['id_conta'])

            session['saldo'] = valorContaOrigem

            funcs.Transacao(conta_origem=IdContaOrigem, conta_destino=IdContaDestino, tipo='transferencia', valor=float(request.form['valor']), status='1')
            funcs.email(conta_origem=IdContaOrigem, tipo='transferencia', valor=float(request.form['valor']))
            return Transacao()
    return Transacao()
        
#------------------------------

#Página configurações

@app.route("/Config")
def Config():
    return render_template("u_config.html")

#------------------------------

#Página Sua Conta
@app.route("/SuaConta")
def SuaConta():
    return render_template("homenew.html")

#------------------------------

#Bloco de requisição de Abertura de Conta

@app.route("/AceiteContaTabela")
def AceiteContaTabela():

    cabecalho = ('Nome', 'CPF', 'Número Conta', 'Data Nasc', 'Endereço', 'Genero', 'Tipo Conta', '', '')

    pesquisaSQL = funcs.SlcEspecificoMySQL(TabelaBd='tb_usuario INNER JOIN tb_contabancaria ON tb_usuario.id_usuario = tb_contabancaria.id_usuario',
                                           CampoEs=['tb_contabancaria.id_conta','tb_usuario.nome', 'tb_usuario.cpf', 'tb_contabancaria.numeroconta','tb_usuario.datanascimento','tb_usuario.endereco','tb_usuario.genero', 'tb_contabancaria.tipo'],
                                           CampoBd=['tb_contabancaria.status_contabancaria'],
                                           CampoFm=[0])

    return render_template("AceiteConta.html", cabecalhoTabela=cabecalho, pesquisaSQLTabela=pesquisaSQL)

@app.route("/AceiteAlteracaoTabela")    
def AceiteAlteracaoTabela():

    cabecalho = ('Nome', 'CPF', 'Data Nasc', 'Número Conta', 'Tipo Conta', 'Descrição')

    pesquisaSQL = funcs.SlcEspecificoMySQL(TabelaBd='tb_usuario INNER JOIN tb_contabancaria ON tb_usuario.id_usuario = tb_contabancaria.id_usuario INNER JOIN tb_requisicoes ON tb_usuario.id_usuario = tb_requisicoes.id_usuario',
                                           CampoEs=['tb_contabancaria.id_conta', 'tb_usario.id_usuario','tb_usuario.nome', 'tb_usuario.cpf', 'tb_contabancaria.numeroconta','tb_usuario.datanascimento', 'tb_contabancaria.tipo' , 'tb_requisicoes'],
                                           CampoBd=['status_alteracao'],
                                           CampoFm=[0])

    return render_template("ReqAlt.html", cabecalhoTabela=cabecalho, pesquisaSQLTabela=pesquisaSQL)

@app.route("/ReqAlt")
def ReqAlt():
    return render_template('ReqAlt.html')


@app.route("/Cancelamento")
def Cancelamento():
    return render_template('cancelamento.html')

@app.route("/CancelamentoConta",  methods = ['POST', 'GET'])
def CancelamentoConta():
    if request.method == 'POST':
        id_usuario = funcs.SlcEspecificoMySQL(TabelaBd='tb_contabancaria INNER JOIN tb_usuario ON tb_contabancaria.id_usuario = tb_usuario.id_usuario ',
                                             CampoBd=['numeroconta'],
                                             CampoFm=[session['conta']],
                                             CampoEs=['tb_usuario.id_usuario'])
        senha = request.form['senha']
        funcs.cancelMySQL(id_usuario = id_usuario[0][0], senha= senha, numeroconta= session['conta'])
        

#------------------------------

#Bloco de requisição de Abertura de Conta

@app.route("/RequisicaoAberturaConta")
def RequisicaoAberturaConta():
    return render_template('RequisicaoAberturaConta.html')

@app.route("/AberturaConta", methods = ['POST', 'GET'])
def AberturaConta():
    if request.method == 'POST':

        tipoConta = request.form['tipoconta']
        conta = session['conta']

        pesquisaUsario = funcs.SlcEspecificoMySQL(TabelaBd='tb_contabancaria INNER JOIN tb_usuario ON tb_usuario.id_usuario = tb_contabancaria.id_usuario',
                                           CampoEs=['tb_usuario.id_usuario', 'tb_usuario.cpf', 'tb_usuario.nome'],
                                           CampoBd=['numeroconta'],
                                           CampoFm=[conta])
        
        idUsuario = pesquisaUsario[0][0]
        cpf = pesquisaUsario[0][1]
        nome = pesquisaUsario[0][2]
        numeroConta = funcs.geraId(str(nome),str(1),str(cpf))
        
        funcs.InsMySQL(TabelaBd='tb_contabancaria',
                        CampoBd=['tipo', 'id_usuario', 'id_agencia', 'numeroconta', 'data_abertura', 'saldo', 'status_contabancaria'],
                        CampoFm=[tipoConta, idUsuario, 1, numeroConta, datetime.today(), 0, '0'])    

        return RequisicaoAberturaConta()

#------------------------------

#Bloco de alteração do saldo do banco

@app.route("/AltSaldo",  methods = ['POST', 'GET'])
def AltSaldo():
    if request.method == 'POST': 
        NovoSaldoBK = request.form['ValNovoSaldo']
        session['saldo'] =float(NovoSaldoBK)
        funcs.upMySQL('tb_capitaltotal',CampoBd=['capitalinicial'],CampoFm=[NovoSaldoBK],CampoWr=['id_capitaltotal'],CampoPs=['1'])
        
    saldo = f"{session['saldo']:.2f}".replace(".",",")
    saldoV = f"{session['saldo']:.2f}"
    return render_template('AltSaldo.html',saldo=saldo,saldoV=saldoV)    
#------------------------------

#Tratamento de Erros
# @app.errorhandler(Exception)
# def excecao(e):
#     cod_excecao = str(e)
#     cod_excecao = cod_excecao[:3]
#     print(f'{cod_excecao} - {funcs.erro[cod_excecao]}')
#     return render_template("erro.html", cod_erro=cod_excecao, desc_erro=funcs.erro[cod_excecao])


#Bloco para subir o site.
if __name__ == "__main__":
     app.run(debug=True)
