
import sys
import logging
import rds_config
import pymysql



logger = logging.getLogger()
logger.setLevel(logging.INFO)

#rds settings
rds_host  = "mysqlforroombooking.chumz9r1slpo.eu-west-1.rds.amazonaws.com"
name = rds_config.db_username
password = rds_config.db_password
db_name = rds_config.db_name


	

bookings=[]

try:
        conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
except:
        logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")

def setBooking(room,day,month,time):
        item_count = 0
        with conn.cursor() as cur:
            cur.execute("select * from rmBooker")
            for row in cur:
                item_count += 1
                logger.info(item_count)
            item_count += 1
            cur.execute('insert into rmBooker (BookingId, Room, Day, Month, Time, Name) values(%s, %s, %s, %s, %s, "Pete")',(item_count,room,day,month,time))
            conn.commit()
        logger.info("Records Inserted")
        return True
    

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
  
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the B T meeting room booking system. " \
                    "Please tell me which room you would like to book " \
                    "and for when by saying, " \
                    "Can i book room three fifteen for the fourth of may at 10 o clock"
   
   
    reprompt_text = ""
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for using the B T meeting room booking service. " \
                    "Have a nice day! "
    
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))



        
def checkAvailability(room,day,month,time):
        item_count = 0
        with conn.cursor() as cur:
            cur.execute("select * from rmBooker where day=%s AND time=%s",(day, time))
            for row in cur:
                item_count += 1
                logger.info(row)
        if item_count ==0:
            return setBooking(room,day,month,time)
        return False
   
def validDate(day,month):
    if month.lower() == "february" and (day.lower() == "29th" or day.lower()=="30th" or day.lower()=="31st"):
        return False
    if day.lower() == "31st" and (month.lower() =="september" or month.lower() == "april" or month.lower()=="june" or month.lower()=="november"):
        return False
    return True
    
def getBookings(room,day,month):
    item_count = 0
    speech = "The current bookings for " + room+" are "
    with conn.cursor() as cur:
        cur.execute("select * from rmBooker where room=%s AND day=%s AND month=%s",(room, day, month))
        result_set = cur.fetchall()
        for row in result_set:
            speech += row[0] + ' o clock '
            item_count += 1
            logger.info(row)
    if item_count == 0:
        speech = "there are no bookings for this room"
    return speech
    
    
def get_bookings(intent, session):
    card_title = intent['name']
    session_attributes = {}
    should_end_session = False
    if 'Room' in intent['slots'] and 'Day' in intent['slots'] and 'Month' in intent['slots']:
        room = intent['slots']['Room']['value']
        day = intent['slots']['Day']['value']
        month = intent['slots']['Month']['value']
        speech_output = getBookings(room,day,month)
        reprompt_text = ''
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))
    
def set_booking_details(intent, session):
    card_title = intent['name']
    session_attributes = {}
    should_end_session = False
    speech_output=''
    reprompt_text = ''
    if 'Room' in intent['slots'] and 'Day' in intent['slots'] and 'Month' in intent['slots'] and 'Time'in intent['slots']:
        room = intent['slots']['Room']['value']
        day = intent['slots']['Day']['value']
        month = intent['slots']['Month']['value']
        time = intent['slots']['Time']['value']
        if validDate(day,month):
            if checkAvailability(room,day,month,time):
                speech_output = "room " + room + "is booked on the " + day + " of " + month + "at " + time + " o clock"
            else:
                speech_output = "sorry its not available"
        else:
            speech_output = "There is no date the " + day + " of " + month

    else:
        speech_output = "I didn't get enough information to book a room. " \
                        "Please try again."
        reprompt_text = "please try again"
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        



# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']


    if intent_name == "BookingDetails":
        return set_booking_details(intent,session)
    elif intent_name == "ListBookings":
        return get_bookings(intent,session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])



	

