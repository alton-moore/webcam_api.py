

# Sample API program for SunGard from Alton Moore, aomoore3@gmail.com, 956-581-5577 cell/SMS
#
# I have an existing webcam system written in PHP, so this gives a little bit of API access
# to it for you to play around with.  This is my first go at using Flask, but it seems fairly
# straightforward, and I'll learn more as I use it for more substantial projects.  I really am
# at a loss as to what to include in this program for you, since this business of making up
# something to send in to you is not amenable to my regular process of analysing the situation,
# so to speak.  So I've just come up with these few endpoints, and you can tell me if you want
# something elaborated upon.
#
# I don't know if you were looking for an example of authentication here, but it's pretty trivial,
# consisting mostly of copying a few lines from an example on line to a /login endpoint for POSTs.
# Since authentication standards vary from company to company, I haven't bothered to do this, but
# if you want, we can do the truly random token, store it in a database with expiration time, and
# require and check it on every call, that sort of thing.
#
# You'll notice that I like long lines, but that is just my personal style, and I'm willing to
# conform if company standards differ.  Seems like I get more on the screen that way though.
# Yes, I have read PEP8!  ;-)
#
# I am returning some fairly verbose strings for you; I know that most 200s would probably just
# say "OK" and be done with it.  I also print a little bit on the screen for my own information.


# Modules used in more than one place
from flask import Flask, abort

# This API runs on the same server that the webcam system runs on, and we want to read from a couple of data files.
data_file_directory     = '/utility/webcams/'
graphics_file_directory = '/var/www/'
snapshots_directory     = '/var/www/snapshot_files/'
#
webcam_data_file_name = data_file_directory + 'webcams.dat'


# Get the Flask object created and make sure that debugging is turned off.
app = Flask(__name__)
app.debug = False  # This option should always be off for production, since it allows the execution of arbitrary commands.


#---------- Subroutines ----------

def return_webcam_directory(webcam_number):  # The 4th column of data in the webcam data file is a directory name.
    webcam_data_file = open(webcam_data_file_name)
    webcam_directory = ''
    line_number = 0
    for line in webcam_data_file.readlines():  # Read file line by line until we get to the proper line number.
        line_number += 1
        if line_number == webcam_number:
            webcam_directory = line.split(',')[3]
            break
    webcam_data_file.close()
    return webcam_directory


#------------------------------- Endpoints -------------------------------

@app.route('/')  # A small help screen, although I suppose one could also redirect to authentication or the like.
def instructions():
    return app.response_class(
      '<HTML><HEAD><TITLE>API Help</TITLE></HEAD><BODY><PRE>                          \n' +
      'Endpoints:                                                                     \n' +
      '<P>                                                                            \n' +
      '/deletion_form       -- Presents form to test POST operation (with approval)   \n' +
      '/list                -- Lists Alton\'s webcam numbers and descriptions in JSON \n' +
      '/snapshot/#/ddd/hhmm -- Returns the snapshot for ddd (Sun-Sat) at time hhmm    \n' +
      '/view/#              -- Returns the latest image for a given webcam            \n' +
      '</PRE></BODY></HTML>', mimetype='text/html')


@app.route('/deletion_form')    # Not a true API function, but provides a form to a browser to test the snapshot deletion endpoint.
def deletion_form():            # I previously had a POST to a /delete endpoint, but I figured that heading toward the same /snapshot
    return app.response_class(  # endpoint and pretending we had used the DELETE method would be a better example than doing that.
      '<HTML><HEAD><TITLE>Deletion Test Form</TITLE></HEAD><BODY>      \n' +
      '<FORM ACTION="/snapshot/1/Sun/0000" METHOD="POST">              \n' +
      '<P>Camera number: <INPUT TYPE="text"   NAME="camera_number">    \n' +
      '<P>Day of week:   <INPUT TYPE="text"   NAME="day_of_week">      \n' +
      '<P>HHMM:          <INPUT TYPE="text"   NAME="hhmm">             \n' +
      '<P><INPUT TYPE=submit VALUE=Delete></FORM>                      \n' +
      '</BODY></HTML>', mimetype='text/html')


@app.route('/list')  # List webcam numbers available for use and their descriptions.
def list_webcams():
    import json  # I like to import things where they are used if they are only used in one place.
    #
    webcam_data_file = open(webcam_data_file_name)
    line_number = 0
    webcam_list = []
    for line in webcam_data_file.readlines():
        line_number += 1  # The webcam number corresponds to its line number in the data file.
        webcam_description = line.split(',')[0]
        webcam_list.append([line_number,webcam_description])
    webcam_data_file.close()
    # Flask has the jsonify() method, but this works fine; just depends on what you want in the JSON I guess.
    return app.response_class(json.dumps(dict(webcam_list), indent=None), mimetype='application/json')


@app.route('/snapshot/<int:webcam_number>/<day_of_week>/<hhmm>', methods=['GET','POST'])  # View/delete snapshot for webcam, day of week, and HHMM.
def view_snapshot(webcam_number, day_of_week, hhmm):
    from flask import request
    #
    # Here we would usually check for the DELETE method, but our little sample deletion form can't use that method or
    # construct the URL properly either one, so we're faking that functionality instead.  I could have checked for DELETE,
    # but you probably want to see the program work without having to make up your own calls to it, so there you go.
    if request.method == 'POST':  # Just pretend this is a DELETE.  ;-)  Among other things, since the code's different too.
        import os
        #
        filespec_to_delete = snapshots_directory                      +  \
          return_webcam_directory(int(request.form['camera_number'])) +  \
                                '/' + request.form['day_of_week']     +  \
                                '/' + request.form['hhmm'] + '.jpg'
        print 'Trying to delete filespec ' + filespec_to_delete
        try:
            os.remove(filespec_to_delete)
        except:
            abort(404)  # They must have passed invalid webcam number, day of week, or hhmm, or file was deleted already.
        return 'Success; deleted filespec ' + filespec_to_delete
    #
    webcam_directory = return_webcam_directory(webcam_number)  # No need to check this result, since the try/except will anyway.
    try:
        webcam_jpg_file = open(snapshots_directory + webcam_directory + '/' + day_of_week + '/' + hhmm + '.jpg')
    except:
        abort(404)  # This line means the camera number, day of week, and/or time was invalid.
    jpg_content = webcam_jpg_file.read()
    webcam_jpg_file.close()
    return app.response_class(jpg_content, mimetype='image/jpg')


@app.route('/view/<int:webcam_number>')  # Returns most recent image for a given webcam.
def view_most_recent(webcam_number):
    try:
        webcam_jpg_file = open(graphics_file_directory + 'webcam' + str(webcam_number) + '.jpg')
    except:
        abort(404)  # This means the webcam number supplied was invalid.
    jpg_content = webcam_jpg_file.read()
    webcam_jpg_file.close()
    return app.response_class(jpg_content, mimetype='image/jpg')


#-------------------- Invokes the program and specifies which IP(s) to listen on --------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0')


