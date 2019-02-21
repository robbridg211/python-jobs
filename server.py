from flask import Flask, render_template, session, request, redirect, flash
# import the function connectToMySQL from the file mysqlconnection.py
from mysqlconnection import connectToMySQL
import datetime
import re
from flask_bcrypt import Bcrypt
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
app = Flask(__name__)
app.secret_key = 'SecretsSecretsAreNoFun,SecretsSecretsHurtSomeone'
bcrypt = Bcrypt(app)
# invoke the connectToMySQL function and pass it the name of the database we're using
# connectToMySQL returns an instance of MySQLConnection, which we will store in the variable 'mysql'

def check_login():
    if 'id' not in session or session['id'] == None:
        return False
    return True

@app.route('/')
def index():
    if 'id' not in session:
        session['id'] = None
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    session.clear()
    messages = False
                ######## first name registration validation #######
    if len(request.form['first_name']) < 1:
        flash(f"<span style='color: red'>*Missing Field Required</span>", 'first_name')
        messages = True
    if len(request.form['first_name']) < 2:
        messages = True
        flash(f"<span style='color: red'>*First name must be 2+ characters</span>", 'first_name')

            ######## last name registration validation #######
    if len(request.form['last_name']) < 1:
        messages = True
        flash(f"<span style='color: red'>*Missing Field Required</span>", 'last_name')
    if len(request.form['last_name']) < 2:
        messages = True
        flash(f"<span style='color: red'>*Last name must be 2+ characters</span>", 'last_name')

            ######## email registration validation #######
    if len(request.form['email']) < 1:
        messages = True
        flash(f"<span style='color: red'>*Missing Field Required</span>", 'email')
    if not EMAIL_REGEX.match(request.form['email']):
        messages = True
        flash(f"<span style='color: red'>*Format Invalid for Email Address</span>", 'email')

            ######## password registration validation #######
    if len(request.form['password']) < 8:
        messages = True
        flash(f"<span style='color: red'>*Password must be atleast 8 characters</span>", 'password')
    if (request.form['confirmpassword'] != request.form['password']):
        messages = True
        flash(f"<span style='color: red'>*Passwords do not match</span>", 'confirmpassword')

              ######## email registration validation (if exists) #######
    emailQuery = "SELECT * FROM users WHERE email = %(email)s;"
    data = {"email" : request.form['email']}
    mysql = connectToMySQL("handy_helper")
    results = mysql.query_db(emailQuery, data)
    if results:
        flash(f"<span style='color: red'>*{request.form['email']} already exists. Try Again</span>", 'email')
    elif messages == True:
        return redirect('/')
    else:
        pw_hash = bcrypt.generate_password_hash(request.form['password'])  
        mysql = connectToMySQL("handy_helper")
        query = "INSERT INTO users (`first_name`,`last_name`,`email`, `password`, `created_at`, `updated_at`) VALUES (%(first_name)s, %(last_name)s, %(email)s, %(password_hash)s, %(created_at)s, %(updated_at)s );"
        data = {
            "first_name": request.form["first_name"],
            "last_name": request.form["last_name"],
            "email": request.form["email"],
            "password_hash": pw_hash,
            "created_at": datetime.datetime.now(),
            "updated_at" : datetime.datetime.now()
        }
        newUser = mysql.query_db(query, data)
        session['id'] = newUser
        print(session['id'], "register - SESSION")
        return redirect('/dashboard')
    return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    session.clear()
    if len(request.form['email']) < 1:
        flash(f"<span style='color: red'>*Missing Field Required</span>",'log_email')
    elif not EMAIL_REGEX.match(request.form['email']):
        flash(f"<span style='color: red'><br/>*Format Invalid for Email Address</span>", 'log_email')
    if len(request.form['password']) < 1:
        flash(f"<span style='color: red'>*Missing Field Required</span>",'log_password')
    mysql = connectToMySQL("handy_helper")
    query = "SELECT * FROM users WHERE email = %(email)s;"
    data = {"email" : request.form['email']}
    result = mysql.query_db(query, data)
    if result:
        if bcrypt.check_password_hash(result[0]['password'], request.form['password']):
            session['id'] = result[0]['id']
            return redirect('/dashboard')
        else:
            flash(f"<span style='color: red'><br/>*Password Incorrect</span>", 'log_password')
            return render_template('index.html')
    else:
        flash(f"<span style='color: red'>*Email Doesn't Exist</span>", 'log_email')

    return redirect('/')

@app.route('/dashboard')
def dash():
    if check_login():
    #query to get the header first name to display
        mysql = connectToMySQL('handy_helper')
        query = "SELECT users.first_name FROM users WHERE id = %(id)s;"
        data = {"id" : session['id']}
        name = mysql.query_db(query, data)
        firstName = name[0]['first_name']

        mysql=connectToMySQL('handy_helper')
        query = "SELECT jobs.id, jobs.title, jobs.location, jobs.users_id FROM jobs JOIN users ON users.id = jobs.users_id ORDER BY jobs.updated_at DESC;"
        jobs = mysql.query_db(query)
        
        return render_template('dashboard.html', firstName=firstName, jobs=jobs)

    else:
        return redirect('/')

@app.route('/view/<id>')
def viewJob(id):
    if check_login():
        mysql = connectToMySQL('handy_helper')
        query = "SELECT users.first_name FROM users WHERE id = %(id)s;"
        data = {"id" : session['id']}
        name = mysql.query_db(query, data)
        firstName = name[0]['first_name']

        #query to view further info about clicked on job
        mysql = connectToMySQL('handy_helper')
        query = "SELECT jobs.id, jobs.title, jobs.description, jobs.location, users.first_name, users.last_name, jobs.created_at FROM jobs JOIN users ON users.id = jobs.users_id WHERE jobs.id = %(id)s;"
        data = {'id': id}
        viewedJob = mysql.query_db(query, data)
    
        return render_template('view.html', firstName=firstName, viewedJob=viewedJob)
    else:
        return redirect('/')

@app.route('/edit/<id>')
def edit(id):
    if check_login():
        mysql = connectToMySQL('handy_helper')
        query = "SELECT users.first_name FROM users WHERE id = %(id)s;"
        data = {"id" : session['id']}
        name = mysql.query_db(query, data)
        firstName = name[0]['first_name']

        mysql = connectToMySQL('handy_helper')
        query = "SELECT jobs.id, jobs.title, jobs.description, jobs.location, users.first_name, users.last_name, jobs.created_at FROM jobs JOIN users ON users.id = jobs.users_id WHERE jobs.id = %(id)s;"
        data = {'id': id}
        editJob = mysql.query_db(query, data)
        location = editJob[0]['location']
        title = editJob[0]['title']
        description = editJob[0]['description']

        return render_template('edit.html', id=id, firstName=firstName, location=location, title=title, description=description, editJob=editJob )
    else:
        return redirect('/')


@app.route('/edit/<id>', methods=['POST'])
def editJob(id):
    if check_login():
        if len(request.form['title']) < 3:
            flash(f"<span style='color: red'><br />*Insufficient Information Provided, Try Again</span>", 'noEdit')
            return redirect('/edit/'+id)

        elif len(request.form['description']) < 3:
            flash(f"<span style='color: red'><br />*Insufficient Information Provided, Try Again</span>", 'noEdit')

            return redirect('/edit/'+id)
        elif len(request.form['location']) < 3:
            flash(f"<span style='color: red'><br />*Insufficient Information Provided, Try Again</span>", 'noEdit')
            return redirect('/edit/'+id)

        else:
            #edit job posting
            mysql = connectToMySQL("handy_helper")
            query = "UPDATE jobs SET jobs.title = %(title)s, jobs.description = %(description)s, jobs.location = %(location)s WHERE (id = %(id)s);"
            data = {
                "title" : request.form['title'],
                "description" : request.form['description'],
                "location" : request.form['location'],
                "id" : id
            }
            print(data, "DAAAAAAAAAAAATA")
            mysql.query_db(query, data)
            flash(f"<span style='color: green'>*Job Updated Successfully</span>", 'edit')
            return redirect('/dashboard')

    return redirect('/')


@app.route('/addJob')
def addJob():
    if check_login():
        mysql = connectToMySQL('handy_helper')
        query = "SELECT users.first_name FROM users WHERE id = %(id)s;"
        data = {"id" : session['id']}
        name = mysql.query_db(query, data)
        firstName = name[0]['first_name']
        
    return render_template('add.html', firstName=firstName)

@app.route('/jobs/new', methods=['POST'])
def newJob():
    if check_login():
        if len(request.form['title']) < 3:
            flash(f"<span style='color: red'>*Insufficient Information Provided, Try Again</span>", 'noAdd')
            return redirect('/addJob')
        if len(request.form['description']) < 3:
            flash(f"<span style='color: red'>*Insufficient Information Provided, Try Again</span>", 'noAdd')
            return redirect('/addJob')
        if len(request.form['location']) < 3:
            flash(f"<span style='color: red'>*Insufficient Information Provided, Try Again</span>", 'noAdd')
            return redirect('/addJob')
        else:
            mysql = connectToMySQL("handy_helper")
            query = "INSERT INTO jobs (jobs.title, jobs.description, jobs.location, jobs.created_at, jobs.updated_at, users_id) VALUES (%(title)s, %(description)s, %(location)s, %(created_at)s, %(updated_at)s, %(users_id)s);"
            data = {
                "title": request.form["title"],
                "description": request.form["description"],
                "location": request.form["location"],
                "created_at" : datetime.datetime.now(), 
                "updated_at" : datetime.datetime.now(),
                "users_id" : session['id']
            }
            newJob = mysql.query_db(query, data)
            print(newJob, "joooooooooooooob2")
            flash(f"<span style='color: green'>*Job Added Successfully</span>", 'added')
            return redirect('/dashboard')
    return redirect('/')



@app.route("/delete/<id>")
def delete(id):
    print(id)
    mysql=connectToMySQL('handy_helper')
    query = "DELETE FROM jobs WHERE id = %(id)s;"
    data = {"id" : id}
    mysql.query_db(query, data)
    return redirect('/dashboard')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)

