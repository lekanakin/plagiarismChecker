from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.SimilarityDB
users = db["Users"]

def UserExist(username):
    if users.find({"Username":username}).count()== 0:
        return False
    else:
        return True

class Register(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        if UserExist(username):
            retJson = {
                "status": 301,
                "msg": "Sorry, an account exists for this user"
            }
            return jsonify(retJson)

        hashed_pw =bcrypt.hashpw(password.encode('utf8'),bcrypt.gensalt())

        users.insert({
            "Username": username,
            "Password": hashed_pw,
            "Tokens": 6
        })

        retJson = {
            "status": 200,
            "msg": "You have successfully created an account"
        }
        return jsonify(retJson)

def verifyPw(username,password):
    if not UserExist(username):
        return False

    hashed_pw = users.find({
        "Username":username
    })[0]["Password"]

    if bcrypt.hashpw(password.encode('utf8'), hashed_pw)==hashed_pw:
        return True
    else:
        return False

def countTokens(username):
    tokens = users.find({
        "Username":username
    })[0]["Tokens"]
    return tokens

class Detect(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        text1 = postedData["text1"]
        text2 = postedData["text2"]

        if not UserExist(username):
            retJson= {
                "status": 301,
                "message": "Invalid Username"
            }
            return jsonify(retJson)

        correct_pw = verifyPw(username, password)

        if not correct_pw:
            retJson = {
                "status": 302,
                "msg": "Invalid Password"
            }

        num_tokens = countTokens(username)

        if num_tokens <=0:
            retJson = {
                "status":303,
                "message":"Not enough tokens. Please refill"
            }
            return jsonify (retJson)

#Build  the text siminilary checker
        nlp = spacy.load('en_core_web_sm')

        text1 = nlp(text1)
        text2 = nlp(text2)

        #Ratio is a number between 0 and 1. The closer the to 1, the more similar the sentence
        ratio = text1.similarity(text2)

        #verdict of similarity
        if ratio > 0.5:
            ratioT = "There is a major similarity"
        else:
            ratioT = "There is no major similarity"


        retJson = {
            "status":200,
            "similarity": ratio,
            "verdict":ratioT,
            "message": "similarity score calculated successfully"
        }

        current_tokens =countTokens(username)

        users.update({
            "Username": username,
        }, {
            "$set":{
                "Tokens": current_tokens-1
            }
        })

        return jsonify(retJson)


class Refill(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["admin_pw"]
        refill_amount = postedData["refill"]

        if not UserExist(username):
            retJson = {
                "status":301,
                "msg": "Invalid Username"
            }
            return jsonify(retJson)

        correct_pw = "abc123"
        if not password == correct_pw:
            retJson = {
                "status":304,
                "msg": "Invaid Admin Password"
            }
            return jsonify(retJson)

        current_tokens = countTokens(username)

        users.update({
            "Username": username
        }, {
            "$set":{
                "Tokens":refill_amount + current_tokens
            }
        })

        retJson = {
            "status": 200,
            "msg": "Refilled successfully"
        }
        return jsonify(retJson)


api.add_resource(Register, '/register')
api.add_resource(Detect, '/detect')
api.add_resource(Refill, '/refill')



if __name__ == "__main__":
    app.run(host = '0.0.0.0')
