#===========================================================
# YOUR PROJECT TITLE HERE
# YOUR NAME HERE
#-----------------------------------------------------------
# BRIEF DESCRIPTION OF YOUR PROJECT HERE
#===========================================================


from flask import Flask, render_template, request, flash, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import html
import random
import string
import datetime

from app.helpers.session import init_session
from app.helpers.db      import connect_db
from app.helpers.errors  import init_error, not_found_error
from app.helpers.logging import init_logging
from app.helpers.auth    import login_required
from app.helpers.time    import init_datetime, utc_timestamp, utc_timestamp_now


# Create the app
app = Flask(__name__)

# Configure app
init_session(app)   # Setup a session for messages, etc.
init_logging(app)   # Log requests
init_error(app)     # Handle errors and exceptions
init_datetime(app)  # Handle UTC dates in timestamps


#-----------------------------------------------------------
#Login page route
#-----------------------------------------------------------
# @app.get("/")
# def index():
#     return render_template("pages/login.jinja")


#-----------------------------------------------------------
#Login page route
#-----------------------------------------------------------
@app.get("/")
def home():
    if not session.get("logged_in"):
        return redirect("/login")

    with connect_db() as client:
        # Get all the groups from the DB
        sql = """
            SELECT 
                groups.id,
                groups.name

            FROM groups
            JOIN membership ON groups.id = membership.group_id

            WHERE membership.user_id=?

            ORDER BY groups.name ASC
        """
        # get our user id from the session
        uid = session["user_id"]
        # Get the groups we belong to
        params=[uid]
        result = client.execute(sql, params)
        groups = result.rows

    return render_template("pages/home.jinja", groups=groups)

#-----------------------------------------------------------
# Things page route - Show all the things, and new thing form
#-----------------------------------------------------------
@app.get("/things/")
def show_all_things():
    with connect_db() as client:
        # Get all the things from the DB
        sql = """
            SELECT things.id,
                   things.name,
                   users.name AS owner

            FROM things
            JOIN users ON things.user_id = users.id

            ORDER BY things.name ASC
        """
        params=[]
        result = client.execute(sql, params)
        things = result.rows

        # And show them on the page
        return render_template("pages/things.jinja", things=things)


#-----------------------------------------------------------
# Thing page route - Show details of a single thing
#-----------------------------------------------------------
@app.get("/thing/<int:id>")
def show_one_thing(id):
    with connect_db() as client:
        # Get the thing details from the DB, including the owner info
        sql = """
            SELECT things.id,
                   things.name,
                   things.price,
                   things.user_id,
                   users.name AS owner

            FROM things
            JOIN users ON things.user_id = users.id

            WHERE things.id=?
        """
        params = [id]
        result = client.execute(sql, params)

        # Did we get a result?
        if result.rows:
            # yes, so show it on the page
            thing = result.rows[0]
            return render_template("pages/thing.jinja", thing=thing)

        else:
            # No, so show error
            return not_found_error()


#-----------------------------------------------------------
# Route for adding a thing, using data posted from a form
# - Restricted to logged in users
#-----------------------------------------------------------
@app.post("/add")
@login_required
def add_a_thing():
    # Get the data from the form
    name  = request.form.get("name")
    price = request.form.get("price")

    # Sanitise the text inputs
    name = html.escape(name)

    # Get the user id from the session
    user_id = session["user_id"]

    with connect_db() as client:
        # Add the thing to the DB
        sql = "INSERT INTO things (name, price, user_id) VALUES (?, ?, ?)"
        params = [name, price, user_id]
        client.execute(sql, params)

        # Go back to the home page
        flash(f"Thing '{name}' added", "success")
        return redirect("/things")


#-----------------------------------------------------------
# Route for deleting a thing, Id given in the route
# - Restricted to logged in users
#-----------------------------------------------------------
@app.get("/delete/<int:id>")
@login_required
def delete_a_thing(id):
    # Get the user id from the session
    user_id = session["user_id"]

    with connect_db() as client:
        # Delete the thing from the DB only if we own it
        sql = "DELETE FROM things WHERE id=? AND user_id=?"
        params = [id, user_id]
        client.execute(sql, params)

        # Go back to the home page
        flash("Thing deleted", "success")
        return redirect("/things")







    
#-----------------------------------------------------------
# User create group form route
#-----------------------------------------------------------
@app.get("/group/new")
def create_group_form():
    return render_template("pages/group_create_form.jinja")


#-----------------------------------------------------------
# Route for creating a group when create form submitted
#-----------------------------------------------------------
@app.post("/group")
@login_required
def create_group():
    # Get the data from the form
    name = request.form.get("name")

    # Sanitise the name
    name = html.escape(name)

    with connect_db() as client:
        # Get user id from session
        user_id = session["user_id"]

        # Generate a random join code
        code = ''.join(random.choice(string.ascii_letters) for _ in range(5))

        # Add the group to the groups table
        sql = "INSERT INTO groups (name, owner, code) VALUES (?, ?, ?)"
        params = [name, user_id, code]
        result = client.execute(sql, params)
        new_group_id = result.last_insert_rowid

        # Add us to the group as a member
        sql = "INSERT INTO membership (group_id, user_id) VALUES (?, ?)"
        params = [new_group_id, user_id]
        client.execute(sql, params)

        return redirect("/")



#-----------------------------------------------------------
# User join form route
#-----------------------------------------------------------
@app.get("/group/join")
def join_group_form():
    return render_template("pages/group_join_form.jinja")


#-----------------------------------------------------------
# Root for event page
#-----------------------------------------------------------
@app.get("/group/<int:id>")
def show_all_events(id):
    if not session.get("logged_in"):
        return redirect("/login")
    
    # session.get("groups.id")

    with connect_db() as client:

        # Get all the groups from the DB
        sql = """
            SELECT 
                groups.id,
                groups.name
            FROM groups
            WHERE id=?
        """
        params=[id]
        result = client.execute(sql, params)

        if result.rows:
            group = result.rows[0]

            # If date is blank then make the box editable and show on the events page
            # Get all the groups from the DB
            sql = """
                SELECT 
                    events.id,
                    events.name,
                    events.date,
                    events.description

                FROM events
                JOIN groups ON events.group_id = groups.id

                WHERE groups.id=?

                ORDER BY events.date ASC
            """

            # Get the groups we belong to
            params=[id]
            result = client.execute(sql, params)
            events = result.rows

            return render_template("pages/group_events.jinja", group=group, events=events)
        
        else:
            return not_found_error()
        
    

#-----------------------------------------------------------
# Root for event details page
#-----------------------------------------------------------
@app.get("/event/<int:id>")
def show_an_event(id):
    with connect_db() as client:
        # Get the thing details from the DB, including the owner info
        sql = """
            SELECT  events.id,
                    events.name,
                    events.date,
                    events.description,
                    events.option_1,
                    events.option_2,
                    events.option_3,
                    events.option_4,
                    events.option_5

            FROM events
            JOIN groups ON events.group_id = groups.id 

            WHERE events.id=?
        """
        params = [id]
        result = client.execute(sql, params)

        # Did we get a result?
        if result.rows:
            # yes, so show it on the page
            event = result.rows[0]
            return render_template("pages/event_details.jinja", event=event)

        else:
            # No, so show error
            return not_found_error()
        
 #-----------------------------------------------------------
# User create event form route
#-----------------------------------------------------------     
@app.get("/event/new")
def create_event_form():
    today = datetime.date.today()
    return render_template("pages/event_create_form.jinja", today=today)

#-----------------------------------------------------------
# Route for creating an event when create form submitted
#-----------------------------------------------------------
@app.post("/event")
@login_required
def create_event():
    # Get the data from the form
    name = request.form.get("name")
    date = request.form.get("date")
    description = request.form.get("description")
    question = request.form.get("question")
    
    #Voting options
    option_1 = request.form.get("option_1")

    # Sanitise the name
    name = html.escape(name)

    with connect_db() as client:
        # Get user id from session
        user_id = session["user_id"]


        # Add the event to the events table
        sql = "INSERT INTO events (name, owner) VALUES (?, ?)"
        params = [name, user_id]
        result = client.execute(sql, params)
        new_group_id = result.last_insert_rowid

        # Add us to the group as a member
        sql = "INSERT INTO membership (group_id, user_id) VALUES (?, ?)"
        params = [new_group_id, user_id]
        client.execute(sql, params)

        return redirect("/")










#-----------------------------------------------------------
# User registration form route
#-----------------------------------------------------------
@app.get("/sign-up")
def sign_up_form():
    return render_template("pages/sign_up.jinja")


#-----------------------------------------------------------
# User login form route
#-----------------------------------------------------------
@app.get("/login")
def login_form():
    return render_template("pages/login.jinja")


#-----------------------------------------------------------
# Route for adding a user when registration form submitted
#-----------------------------------------------------------
@app.post("/add-user")
def add_user():
    # Get the data from the form
    name = request.form.get("name")
    username = request.form.get("username")
    password = request.form.get("password")

    with connect_db() as client:
        # Attempt to find an existing record for that user
        sql = "SELECT * FROM users WHERE username = ?"
        params = [username]
        result = client.execute(sql, params)

        # No existing record found, so safe to add the user
        if not result.rows:
            # Sanitise the name
            name = html.escape(name)

            # Salt and hash the password
            hash = generate_password_hash(password)

            # Add the user to the users table
            sql = "INSERT INTO users (name, username, password_hash) VALUES (?, ?, ?)"
            params = [name, username, hash]
            client.execute(sql, params)

            # And let them know it was successful and they can login
            flash("Registration successful", "success")
            return redirect("/login")

        # Found an existing record, so prompt to try again
        flash("Username already exists. Try again...", "error")
        return redirect("/sign_up")


#-----------------------------------------------------------
# Route for processing a user login
#-----------------------------------------------------------
@app.post("/login-user")
def login_user():
    # Get the login form data
    username = request.form.get("username")
    password = request.form.get("password")

    with connect_db() as client:
        # Attempt to find a record for that user
        sql = "SELECT * FROM users WHERE username = ?"
        params = [username]
        result = client.execute(sql, params)

        # Did we find a record?
        if result.rows:
            # Yes, so check password
            user = result.rows[0]
            hash = user["password_hash"]

            # Hash matches?
            if check_password_hash(hash, password):
                # Yes, so save info in the session
                session["user_id"]   = user["id"]
                session["user_name"] = user["name"]
                session["logged_in"] = True

                # And head back to the home page
                return redirect("/")

        # Either username not found, or password was wrong
        flash("Invalid credentials", "error")
        return redirect("/login")

#-----------------------------------------------------------
# Route for processing a user logout
#-----------------------------------------------------------
@app.get("/logout")
@login_required
def logout():
    # Clear the details from the session
    session.pop("user_id", None)
    session.pop("user_name", None)
    session.pop("logged_in", None)

    # And head back to the login page
    return redirect("/")

