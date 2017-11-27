var express = require('express');
var bodyParser = require('body-parser');
var request = require('request');
var session = require('express-session');
var handlers = require('express-handlebars').create({ defaultLayout: 'main' }); // busca siempre en views/layout el archivo main.handlebars
var app = express();

app.engine('handlebars', handlers.engine);
app.set('view engine', 'handlebars');
//extended: false significa que parsea solo string (no archivos de imagenes por ejemplo)
app.use(bodyParser.urlencoded({extended: false }));

//se inicia el modulo de session
app.use(session({
  secret: 'mys3cr3t',
  resave: false,
  saveUninitialized: true,
  cookie: {secure: false}
}));

//esto lo primero que se ejecuta
app.get('/', (req, res) => {
   res.render('home'); // se pasa el nombre home, y lo busca (renderisa) en views/home.handlebars
});

app.get('/test', function (req, res) {
    var sess = req.session
    if(!sess.token){
        res.redirect("/login")
    }
    else{
      var options = {
          method: 'GET',
          uri: 'http://auth-svc:8081/test', // validamos
          headers: {
            'Authorization':'Bearer ' +sess.token,
            'content-type': 'application/json'
        },
        json:{}
        };

        request(options, function (error, response, body) {//pedimos la generacin del token
           if(!error && response.statusCode == 200){
             console.log(body.status);
             if(body.status == "OK"){
               sess.token = body.token;// guardamos el token que el servicio nos devuelve
               console.log("token recibido:\n");
               console.log(sess.token);
               //res.redirect("/principal");
             } else {
                res.render('login', {status:body.msg});
             }
           }
        });
    }

});

app.get('/login',(req,res) => {
  var sess = req.session
  if(sess.token){
      res.redirect('/Encuestas')
  }else{
      res.render('login');
  }
});

app.get('/register', (req, res) => {
    res.render('register');
});

app.get('/Encuestas', function (req, res) {
  var sess = req.session
  if(sess.token){
        // hago request para obtener todas mis encuestas
        var options = {
                headers: {
                  'Authorization':'Bearer ' + sess.token,
                  'content-type': 'application/json',
                  'Accept': 'application/json'
                },
                json : {},
                uri: "http://tw-svc:8088/tw-svc/all",
                method: "GET"
            }
            request(options, function (error, response, body) {
               if(!error && response.statusCode == 200){
                 console.log(body);
                 console.log(body.status);
                //  state = body.status;
                 if(body.status == "OK"){
                   console.log(body.status);
                   all = body.table;
                   console.log(body.table);
                   res.render('listarEncuestas', {tabla: all});
                 }
                 else {
                    res.send("FAIL TW-SVC/ALL");
                 }
               }
            });
  }
  else{  res.render('home');  }
});

app.get('/crear_Encuesta', (req, res) => {
    res.render('crearEncuesta');
});

app.post('/controlEncuesta', (req, res) => { //llama a la api de twitter para crear la encuesta
    console.log("arrancando1\n");
    var num1 = req.body.hash;
    var num2 = req.body.time;
    var num3 = req.body.name;
    var status;
    var sess = req.session
    var options = {
            method: "POST",
            uri: "http://tw-svc:8088/tw-svc/create",
            headers: {
              'Authorization':'Bearer ' + sess.token,
              'content-type': 'application/json'
            },
            json: { "hash": num1, "time": num2, "surveyname": num3}
        }
        console.log("arrancando2\n");

        request(options, function (error, response, body) {
            if (!error && response.statusCode == 200) {
                 console.log(body.status);
                if (body.status == "OK") {
                  res.redirect("/Encuestas");
                }
                else{
                    res.redirect('/Encuestas', { status: body.msg });
                }
            }
            else{
              console.log("arrancando3\n");
            }

        });
});

app.post('/control', (req, res) => {//controla si lo que se ingresa en login esta bien
    var name = req.body.name;
    var password = req.body.password;
    var sess = req.session;
    var status;

    if(name == '' || password == ''){
      status = 'datos Incorrectos';
      res.render('login', {status:"debe completar los campos..."});
    }else{

      //le enviamos al servico los datos para que controle
      var options = {
              uri: "http://auth-svc:8081/auth-svc/login",
              method: "POST",
              headers: {
                'content-type': 'application/json'
              },
              json: { "user": name, "pass": password }
          };

          request(options, function(error, response, body) {
              if (!error && response.statusCode == 200) {
                  var state = body.status;
                  if (body.status == "OK") {
                    sess.token = body.token;
                    res.redirect('/Encuestas');//debemos mandarlo a otra ventana
                  }
                  else{
                    res.render('login', { status: body.msg });
                  }
              }

          });
    }
});

app.post('/procesar', function (req, res){//controla los campos de la vista registro
    var name = req.body.name;
    var password = req.body.password;
    var password2 = req.body.password2;
    var sess = req.session;
    var status;

    if(name == '' || password == '' || password2 == ''){
      res.render('register', {status:"debe completar todos los campos..."})
    }else if (password != password2){
        res.render('register', { status: 'Passwords do not match' });
    }
    else {
        var options = {//si todo fue bien, se lo mandamos al servicio
            uri: "http://auth-svc:8081/auth-svc/register",
            method: "POST",
            headers: {
              'content-type': 'application/json'
            },
            json: { "username": name, "password": password }
        };

        request(options, function(error, response, body){
            if (!error && response.statusCode == 200) {
                var state = body.status;
                if (body.status == "OK") {
                  sess.token = body.token;
                  res.render('register', { status: 'User created correctly' });
                }
                else{
                  res.render('register', { status: body.msg });
                }
            }
       });
     }
});

app.listen(3000);
