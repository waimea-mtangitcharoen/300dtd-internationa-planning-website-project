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
#Homepage route
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
                groups.name,
                groups.code,
                groups.owner

            FROM groups
            JOIN membership ON groups.id = membership.group_id

            WHERE membership.user_id=?

            ORDER BY groups.id DESC
        """
        # get our user id from the session
        uid = session["user_id"]
        # Get the groups we belong to
        params=[uid]
        result = client.execute(sql, params)
        groups = result.rows

    return render_template("pages/home.jinja", groups=groups)

#-----------------------------------------------------------
# Route for deleting a group, Id given in the route
# - Restricted to logged in users
#-----------------------------------------------------------
@app.get("/delete/<int:id>")
@login_required
def delete_a_group(id):
    # Get the user id from the session
    user_id = session["user_id"]

    with connect_db() as client:
        # Delete the group from the DB only if we own it
        sql = "DELETE FROM groups WHERE id=? AND owner=?"
        params = [id,user_id]
        result = client.execute(sql, params)

        if result.rows_affected == 1:
            # Group was deleted, so remove associated members and events

            sql = "DELETE FROM membership WHERE group_id=?"
            params = [id]
            client.execute(sql, params)

            sql = "DELETE FROM events WHERE group_id=?"
            params = [id]
            client.execute(sql, params)

            flash("Group deleted", "success")

        else:
            flash("Group could not be deleted", "error")

        # Go back to the home page
        return redirect("/")
    
#-----------------------------------------------------------
# Route for deleting an event, id given in the route
# - Restricted to logged in users
#-----------------------------------------------------------
@app.get("/delete/event/<int:id>")
@login_required
def delete_an_event(id):
    # Get the user id from the session
    user_id = session["user_id"]

    with connect_db() as client:
        sql = """
                SELECT groups.owner, events.group_id
                FROM events
                JOIN groups ON events.group_id = groups.id
                WHERE events.id = ?

        """
        params = [id]
        result = client.execute(sql, params)

        # In case the user tries to delete event from the URL that does not exist
        if not result.rows:
            flash("Event not found", "error")
            return("/")
        
        row = result.rows[0]
        owner = row["owner"]
        group_id = row["group_id"]

        if owner == user_id:
            # Delete the group from the DB only if we own it
            sql = "DELETE FROM events WHERE id=?"
            params = [id]
            result = client.execute(sql, params)
        
        # Go back to the home page
        return redirect(f"/group/{ group_id }")
        

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

    # Sanitise the name so the user cannot try to break the website
    name = html.escape(name)

    with connect_db() as client:
        # Get user id from session
        user_id = session["user_id"]

        # Generate a random join code
        code = ''.join(random.choice(string.ascii_letters) for _ in range(5))

        print(code)

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
# User joining a group route
#-----------------------------------------------------------
@app.post("/join-user")
@login_required
def join_user():
    # Get the code from the form
    code = request.form.get("code", "")

    with connect_db() as client:
        code = html.escape(code)

        # Attempt to find a record for that code
        sql = "SELECT id FROM groups WHERE code = ?"
        params = [code]
        result = client.execute(sql, params)

        # Did we find a record?
        if not result.rows:
            flash("The group does not exist", "error")
            return redirect("/group/join")
        
        group = result.rows[0]
        group_id = group["id"]
        user_id = session["user_id"]

        # Check if user is already a member
        sql = "SELECT * FROM membership WHERE user_id = ? AND group_id = ? "
        params = [user_id, group_id]
        result = client.execute(sql, params)

        if not result.rows:
            sql = "INSERT INTO membership (user_id, group_id) VALUES (?, ?)"
            params = [user_id, group_id]
            client.execute(sql, params)
            flash("Join group successful", "success")
            return redirect("/")
        
        flash("You are already a member of this group", "error")
        return redirect("/group/join")

        # Either username not found, or password was wrong
        

#-----------------------------------------------------------
# Root for event page
#-----------------------------------------------------------
@app.get("/group/<int:id>")
def show_all_events(id):
    if not session.get("logged_in"):
        return redirect("/login")

    sort_query = request.args.get('sort') 

    with connect_db() as client:

        # Get all the groups from the DB
        sql = """
            SELECT 
                groups.id,
                groups.name,
                groups.owner
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
            """

            if sort_query:
                sort_query = sort_query.lower()
                if sort_query == 'recent':
                    sql = sql + " ORDER BY events.id DESC"
                elif sort_query == 'date':
                    sql = sql + " ORDER BY events.date ASC"
                else:
                    sql = sql + " ORDER BY events.date DESC"

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
                    events.question,
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
@app.get("/group/<int:id>/newevent")
def create_event_form(id):
    today = datetime.date.today()
    return render_template("pages/event_create_form.jinja", today=today, group_id=id)


#-----------------------------------------------------------
# Route for creating an event when create form submitted
#-----------------------------------------------------------
@app.post("/group/<int:id>/newevent")
@login_required
def create_event(id):
    # Get the data from the form
    name = request.form.get("name","")
    date = request.form.get("date", None)
    description = request.form.get("description", None)
    question = request.form.get("question", None)
    
    #Voting options
    option_1 = request.form.get("option_1", None)
    option_2 = request.form.get("option_2", None)
    option_3 = request.form.get("option_3", None)
    option_4 = request.form.get("option_4", None)
    option_5 = request.form.get("option_5", None)

    # Sanitise any text data
    name = html.escape(name)
    description = html.escape(description) if description else None
    question = html.escape(question) if question else None
    option_1 = html.escape(option_1) if option_1 else None
    option_2 = html.escape(option_2) if option_2 else None
    option_3 = html.escape(option_3) if option_3 else None
    option_4 = html.escape(option_4) if option_4 else None
    option_5 = html.escape(option_5) if option_5 else None

    with connect_db() as client:
    
        group_id = id

        # Add the event to the events table
        sql = "INSERT INTO events (name, date, description, group_id, question, option_1, option_2, option_3, option_4, option_5) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        params = [name, date, description, group_id, question, option_1, option_2, option_3, option_4, option_5]
        result = client.execute(sql, params)


        return redirect(f"/group/{id}")


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

