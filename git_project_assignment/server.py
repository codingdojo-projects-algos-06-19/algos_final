from flask import Flask, session, request, redirect, render_template, flash, url_for
from mysqlconnection import connectToMySQL

app=Flask(__name__)
app.secret_key = 'keep it secret'

from flask_bcrypt import Bcrypt
bcrypt = Bcrypt(app)

import re
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')



'''
*********************************************************
'''

@app.route('/')
def main():
    return render_template('main.html')


@app.route("/users/add", methods=["POST"])
def add_user_to_db():

    is_valid = True
    if len(request.form['first_name']) <= 1:
        is_valid = False
        flash("Please enter a FIRST NAME") # maybe replace flashes with Ajax/jQuery if time allows
    if len(request.form['last_name']) <= 1:
        is_valid = False
        flash("Please enter a LAST NAME")
    if len(request.form['email']) <= 1:
        is_valid = False
        flash("Please enter an EMAIL")
    if not EMAIL_REGEX.match(request.form['email']):
        is_valid = False
        flash("Invalid email address format")
    if len(request.form['password1']) <= 5:
        is_valid = False
        flash("Password must be 5 or more characters")
    if (request.form['password1'] != request.form['password2']):
        is_valid = False
        flash("Passwords do not match!")

    if is_valid:
        mysql = connectToMySQL('great_ideas')
        pw_hash = bcrypt.generate_password_hash(request.form['password1'])
        query = 'INSERT INTO users (first_name, last_name, alias, email, password) VALUES (%(fnm)s, %(lnm)s, %(als)s, %(eml)s, %(psw)s);'
        data = {
            "fnm": request.form['first_name'],
            "lnm": request.form['last_name'],
            "als": request.form['alias'],
            "eml": request.form['email'],
            "psw": pw_hash
        }
        mysql.query_db(query, data)


        session['login'] = True # add this on

        # below we are doing another query for users with this email, and we are storing its id as session['userid']

        mysql2 = connectToMySQL('great_ideas')
        query2 = "SELECT * FROM users WHERE email = %(email2)s;"
        data2 = {
            "email2": request.form["email"]
        }
        result = mysql2.query_db(query2, data2)
        session['userid'] = result[0]['id']
        flash("You've Successfully Added a Friend!")

    return redirect('/users/welcome')
    


@app.route('/users/login', methods=['POST'])
def login():
    mysql = connectToMySQL('great_ideas')
    query = 'SELECT * FROM users WHERE email = %(eml)s;'
    data = {
        "eml": request.form['logemail']
    }
    result = mysql.query_db(query, data)

    if result:
        session['userid'] = result[0]['id']
        hashed_pw = result[0]['password']
        if bcrypt.check_password_hash(hashed_pw, request.form['logpassword']):
            session['login'] = True
            flash("Thanks for logging in")
            return redirect('/users/welcome')
        else:
            session['login'] = False
            flash("Login failed. Please try again or register.")
            return redirect('/')
    else:
        flash("Your email could not be found. Please retry or register.")
        return redirect('/')

'''
******************************************
End of the code needed for main.html
******************************************
'''


@app.route('/users/welcome', methods=['POST', 'GET'])
def welcome():
    if not session['login']:
        flash("You're not logged in. Please login or register")
        return redirect('/')
    else:
        mysql = connectToMySQL('great_ideas')
        query = "SELECT * FROM users WHERE id = %(seid)s;"
        data = {
            "seid": session['userid']
        }

        # Resulting_user is all the information about the specific user who logged in/register
        resulting_user = mysql.query_db(query, data)
        

        mysql2 = connectToMySQL('great_ideas')
        ideaText = "SELECT * FROM users JOIN ideas ON users.id = ideas.user_id WHERE users.id ORDER BY ideas.id DESC;"
        # quoteText = "SELECT * FROM quotes LEFT JOIN users ON quotes.user_id = users.id ORDER BY quotes.id DESC;"
        
        # resultQuote has all the information of users and quotes tied together via users.id = quotes.user_id
        resultIdea = mysql2.query_db(ideaText)

        

        # The multiple join
        # mysql3 = connectToMySQL('quotes_dash2')
        # quoteText2 = "SELECT * FROM users LEFT JOIN quotes ON users.id = quotes.user_id LEFT JOIN likes ON users.id = likes.user_id WHERE quotes.user_id IN (SELECT likes.id FROM likes WHERE likes.user_id = %(_id)s) ORDER BY quotes.id DESC;"
        # data2 = {
        #     "_id": session['userid']
        # }

        mysql3 = connectToMySQL('great_ideas')
        ideaText2 = "SELECT * FROM users JOIN ideas ON users.id=ideas.user_id JOIN likes ON ideas.id=likes.quote_id WHERE users.id = likes.user_id ORDER BY ideas.id DESC;"
        data2 = {
            "_id": session['userid']
        }

        mysql3.query_db(ideaText2, data2)


        return render_template("welcome.html", result_user=resulting_user[0], resultIdeas = resultIdea)





@app.route('/users/logout', methods=['GET'])
def logout():
    session['login'] = False
    flash("You are now logged out. Come back soon!")
    session.clear()
    return redirect('/')





'''
+++++++++++++++++++++++
'''






@app.route('/ideas/create', methods=['POST'])
def write_idea():
    is_valid = True
    if len(request.form['idea_content']) < 10:
        is_valid = False
        flash("The idea must be at least 10 characters long.")
        return redirect('/users/welcome')

    if is_valid:
        mysql = connectToMySQL('great_ideas')
        query = 'INSERT INTO ideas (user_id, idea_content) VALUES (%(userid)s, %(idea)s);'
        data = {
            "userid": session['userid'],
            "idea": request.form['idea_content']
        }
        mysql.query_db(query, data)
        return redirect('/users/welcome')




# I'm going to have to figure out how to include DELETE only on the posts that are associated with that user
# Maybe use an if statement in the template itself

@app.route('/ideas/<id>/delete', methods=['POST'])
def delete_idea(id):
    
    mysql2 = connectToMySQL('great_ideas')
    query2 = 'DELETE FROM likes WHERE idea_id = %(q_id)s'
    data2 = {
        "q_id": id
    }
    mysql2.query_db(query2, data2)

    mysql = connectToMySQL('great_ideas')
    query = 'DELETE FROM ideas WHERE id = %(_id)s;'
    data = {
        "_id": id
    }
    mysql.query_db(query, data)
    return redirect('/users/welcome')

    # var1 = session['userid']
    # var2 = request.form['userDelete'] --> none of this is needed since I check for this in the template
    # if var1 != var2:
    # else:
    #     flash("You can only delete your own quote!")
    #     return redirect("/users/welcome") --> this is not needed because the delete button won't show up for them.








@app.route('/ideas/<id>/add_like', methods=['POST'])
def add_like(id):
    is_valid = True
    mysql2 = connectToMySQL('great_ideas')
    query2 = 'SELECT * FROM likes WHERE user_id = %(us_id)s AND idea_id = %(qu_id)s;'
    data2 = {
        "us_id": request.form["userLike"],
        "qu_id": id
    }
    result2 = mysql2.query_db(query2, data2)

    if result2:
        is_valid = False
        mysql3 = connectToMySQL('great_ideas')
        query3 = 'DELETE FROM likes WHERE idea_id = %(qid)s AND user_id = %(uid)s;'
        data3 = {
            "qid": id,
            "uid": request.form['userLike']
        }
        mysql3.query_db(query3, data3)
        flash("You unliked this.")
    # else:
    #     is_valid = True
    if is_valid:
        mysql = connectToMySQL('great_ideas')
        query = 'INSERT INTO likes (idea_id, user_id) VALUES (%(qid)s, %(uid)s);'
        data = {
            "qid": id,
            "uid": request.form['userLike']
        }
        mysql.query_db(query, data)
        flash("You liked this idea.")

    # mysql4 = connectToMySQL('quotes_dash2')
    # query4 = "SELECT COUNT(user_id) as Those_Who_Like FROM likes WHERE quote_id = %(q_id)s;"
    # data4 = {
    #     "q_id": request.form['quote_ref']
    # }

    # likes = mysql4.query_db(query4, data4)
    # session['numLikes'] = likes



    return redirect('/users/welcome')







@app.route('/users/<id>/view_author')
def view_author(id):
    mysql = connectToMySQL('great_ideas')
    query = "SELECT * FROM ideas WHERE user_id = %(q_id)s;"
    data = {
        "q_id": id
    }
    userIdeas = mysql.query_db(query, data)

    # mysql2 = connectToMySQL('quotes_dash2')
    # query2 = "SELECT * FROM users WHERE id = %(_us_id)s;"
    # data2 = {
    #     "_us_id": request.form['us_id'] # i need the quotes.user_id associated with the quote
    # }

    # ourUser = mysql2.query_db(query2, data2)
    # first = ourUser['first_name']
    # second = ourUser['last_name']

    if len(userIdeas) > 0:
        first = userIdeas[0]['user_id']

    mysql2 = connectToMySQL('great_ideas')
    query2 = 'SELECT * FROM users WHERE id = %(u_id)s;'
    data2 = {
        "u_id": first
    }
    user = mysql2.query_db(query2, data2)
    if len(user) > 0:
        user = user[0]
        # user1 = user[0]['first_name']
        # user2 = user[0]['last_name']

    return render_template('view_author.html', userQuotes= userIdeas, user = user)






# @app.route("/quotes/<id>/unlike")
# def unlikeTweet(id):
#     mysql = connectToMySQL("quotes_dash2")
#     query2 = "DELETE FROM likes WHERE quote_id = %(_id)s;"
#     data2 = {"_id": id }
#     mysql.query_db(query2, data2)
#     flash("You do not like this anymore.")
#     return redirect("/users/welcome")





'''
++++++++++++++++++++++++++++++++++++++

'''



# @app.route('/users/<id>/edit', methods=['GET'])
# def edit_user(id):
#     mysql = connectToMySQL('quotes_dash2')
#     query = 'SELECT * FROM users WHERE id = %(_id)s;'
#     data = {
#         "_id": id
#     }
#     user = mysql.query_db(query, data)
#     if len(user) > 0:
#         user = user[0]

#     return render_template('edit.html', result = user)



# @app.route('/quotes/<id>/update', methods=['POST'])
# def update_tweet(id):
#     mysql2 = connectToMySQL('quotes_dash2')
#     query2 = 'SELECT * FROM users WHERE id = %(_id2)s;'
#     data2 = {
#         "_id2": session['userid']
#     }
#     user2 = mysql2.query_db(query2, data2)
#     if len(user2) > 0:
#         user2 = user2[0]

#     is_valid = True
#     var1 = request.form['email'] # the email they wrote
#     var2 = user2['email']
#     if var1 == var2:
#         is_valid = False
#         flash("Please use a different email address.")
#         return redirect('/users/<id>/edit')
#     if not EMAIL_REGEX.match(request.form['email']):
#         is_valid = False
#         flash("Please use correct email formatting.")
#         return redirect('/users/<id>/edit')

#     if is_valid:
#         mysql = connectToMySQL('quotes_dash2')
#         query = 'UPDATE users SET first_name = %(first)s, last_name = %(last)s, email = %(email)s WHERE id = %(_id)s;'
#         data = {
#             "first": request.form['first_name'],
#             "last": request.form['last_name'],
#             "email": request.form['email'],
#             "_id": id
#         }
#         mysql.query_db(query, data)
#         flash("Thank you for updating your information.")
#         return redirect ('/users/welcome')



if __name__ == ('__main__'):
    app.run(debug=True)