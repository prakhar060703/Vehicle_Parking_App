from app import create_app
# Above line interpreted by Python as:- Looks inside app/__init__.py for create_app()

app = create_app()
# calling the create_app() function (which is defined inside app/__init__.py) 
# and storing its result in the variable app.

if __name__ == '__main__':
    app.run(debug=True)

# This means: Run the Flask server only if this file is executed directly (not imported).
# It prevents the web server from starting accidentally when the file is imported somewhere else.
# It only runs when the file is the main one being executed.
