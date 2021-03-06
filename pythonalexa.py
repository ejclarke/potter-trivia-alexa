from __future__ import print_function
import math
import random
from random import shuffle
import string

# game wide variables
GAME_LENGTH = 630
SKILL_NAME = "The Ultimate Potter Head Quiz"


def lambda_handler(event, context):

    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    # prevent other people from editing the skill
    if (event['session']['application']['applicationId'] !=
            "amzn1.ask.skill.f613a84a-cd5c-479f-b8e0-2e436f673f8e"):
        raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])


def on_session_started(session_started_request, session):
    # call when the session starts
    print("on_session_started requestId=" +
          session_started_request['requestId'] + ", sessionId=" +
          session['sessionId'])


def on_launch(launch_request, session):
    # call when the user launches the skill
    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # call skill launch message
    return get_welcome_response()


def on_intent(intent_request, session):
    # called when user specifies an intent
    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # handle yes/no intent after the user has been prompted
    if session.get('attributes', {}).get('user_prompted_to_continue'):
        del session['attributes']['user_prompted_to_continue']
        if intent_name == 'AMAZON.NoIntent':
            return handle_finish_session_request(intent, session)
        elif intent_name == "AMAZON.YesIntent":
            return handle_repeat_request(intent, session)

    # intent handlers
    if intent_name == "AnswerIntent":
        return handle_answer_request(intent, session)
    elif intent_name == "AnswerOnlyIntent":
        return handle_answer_request(intent, session)
    elif intent_name == "AMAZON.YesIntent":
        return handle_answer_request(intent, session)
    elif intent_name == "AMAZON.NoIntent":
        return handle_answer_request(intent, session)
    elif intent_name == "AMAZON.StartOverIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.RepeatIntent":
        return handle_repeat_request(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return handle_get_help_request(intent, session)
    elif intent_name == "AMAZON.StopIntent":
        return handle_finish_session_request(intent, session)
    elif intent_name == "AMAZON.CancelIntent":
        return handle_finish_session_request(intent, session)
    # potential for multiplayers here
    # elif intent_name == "PlayerIntent":
    #     return ask_for_players()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    # called when the user ends the session
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])


# --------------- Functions that control the skill's behavior -------------


def get_welcome_response():
    intro = ("Welcome to {}. ".format(SKILL_NAME) +
    "This game has over 600 questions. You will hear your score after every 6 questions. You can quit at any point by saying, 'stop'. To hear a question again, just say, 'repeat'. This is a two-player game. The first question is for player one! ")
    
    should_end_session = False
    game_questions = populate_game_questions()
    starting_index = 0

    spoken_question = QUESTIONS[game_questions[starting_index]].keys()[0]

    speech_output = intro + spoken_question
    attributes = {"speech_output": speech_output,
                  "reprompt_text": spoken_question,
                  "current_questions_index": starting_index,
                  "questions": game_questions,
                  "correct_answers": QUESTIONS[game_questions[starting_index]].values()[0],
                  "score1": 0,
                  "score2": 0
                  }

    

    return build_response(attributes, build_speechlet_response(SKILL_NAME,
        speech_output, spoken_question, should_end_session))
        
def populate_game_questions():
    # set index equal to the total number of questions in the game
    index = len(QUESTIONS)

    if GAME_LENGTH > index:
        raise ValueError("Invalid Game Length")

    # make a list of the questions, then shuffle them for randomness
    game_questions = list(range(0, index))
    shuffle(game_questions)

    return game_questions


def handle_answer_request(intent, session):
    attributes = {}
    should_end_session = False
    answer = intent['slots'].get('Answer', {}).get('value')
    user_gave_up = intent['name']



    if 'attributes' in session.keys() and 'questions' not in session['attributes'].keys():
        attributes['user_prompted_to_continue'] = True
        speech_output = "There is no game in progress. " \
                        "Do you want to start a new game?"
        reprompt_text = speech_output
        return build_response(attributes, build_speechlet_response(SKILL_NAME,
                              speech_output, reprompt_text, should_end_session))

    elif not answer and user_gave_up == "DontKnowIntent":
        reprompt = session['attributes']['speech_output']
        speech_output = "Try again," + reprompt
        return build_response(
            session['attributes'],
            build_speechlet_response(SKILL_NAME,
                speech_output, reprompt_text, should_end_session
            ))

    else:
        game_questions = session['attributes']['questions']
        score1 = session['attributes']['score1']
        score2 = session['attributes']['score2']
        current_questions_index = session['attributes']['current_questions_index']
        correct_answers = session['attributes']['correct_answers']
        reprompt_text = session['attributes']['reprompt_text']
        player_num = 1
        
        # set player number based on odd/even questions
        if current_questions_index % 2 != 0:
            player_num = 1
        else:
            player_num = 2

        speech_output_analysis = None
        if answer and answer.lower() in map(string.lower, correct_answers):
            # make sure the right player gets the points
            if (current_questions_index + 1) % 2 == 0:
                    score2 += 1
            else:
                score1 += 1

            speech_output_analysis = "Correct. the next question is for player {} !".format(player_num) if (current_questions_index + 1) % 6 != 0 else "Correct,"


        else:
            if user_gave_up != "DontKnowIntent":
                speech_output_analysis = "Sorry,"
            speech_output_analysis = (speech_output_analysis +
                                      "The correct answer is, " +
                                      correct_answers[0] + ", the next question is for player {} !".format(player_num)) if (current_questions_index + 1) % 6 != 0 else (speech_output_analysis +
                                      "The correct answer is ," +
                                      correct_answers[0] + ",")


        if current_questions_index == GAME_LENGTH - 1:
            speech_output = "" if intent['name'] == "DontKnowIntent" else ""
            final_score = "Player 1 got {} points, Player 2 got {} points. Overall, you got {} out of {} questions correct.".format(score1, score2, (score1 + score2), GAME_LENGTH)
                    
            speech_output = (speech_output + speech_output_analysis +
                             final_score +
                             "Thank you for playing {} with Alexa!".format(SKILL_NAME))
            reprompt_text = ""
            should_end_session = True
            return build_response(
                session['attributes'],
                build_speechlet_response(SKILL_NAME,
                    speech_output, reprompt_text, should_end_session
                ))
        else:
            current_questions_index += 1
            spoken_question = QUESTIONS[game_questions[current_questions_index]].keys()[0]
            reprompt_text = spoken_question
            
            if current_questions_index % 2 == 0:
                player_number = 1
            else:
                player_number = 2
            
            score_check = ("Player 1 has {} points, and Player 2 has {} points. You've gotten {} out of {} questions correct overall. The next question is for player {} !".format(score1, score2, (score1 + score2), (current_questions_index), player_number)) if current_questions_index % 6 == 0 else ""
            speech_output = "" if user_gave_up == "DontKnowIntent" else ""
            speech_output = (speech_output + speech_output_analysis +
                             score_check +
                             reprompt_text)
            attributes = {"speech_output": speech_output,
                          "reprompt_text": reprompt_text,
                          "current_questions_index": current_questions_index,
                          "questions": game_questions,
                          "score1": score1,
                          "score2": score2,
                          "score_check": score_check,
                          "correct_answers": QUESTIONS[game_questions[current_questions_index]].values()[0]  # noqa
                          }

            return build_response(attributes,
                                  build_speechlet_response(SKILL_NAME, speech_output, reprompt_text,
                                                           should_end_session))


def handle_repeat_request(intent, session):
    """
    Repeat the previous speech_output and reprompt_text from the session['attributes'].
    If available, else start a new game session.
    """
    if 'attributes' not in session or 'speech_output' not in session['attributes']:
        return get_welcome_response()
    else:
        attributes = session['attributes']
        speech_output = attributes['speech_output']

        # sloppy, but works - just make sure the !s above are where you want the split
        response, repeat_clause = speech_output.split('!')
        speech_output = "Okay: " + repeat_clause

        reprompt_text = attributes['reprompt_text']

        should_end_session = False
        return build_response(
            attributes,
            build_speechlet_response(SKILL_NAME, speech_output, reprompt_text, should_end_session)

        )


def handle_get_help_request(intent, session):
    attributes = {}
    speech_output = ("You can begin a game by saying start a new game, or, "
                     "you can say exit... What can I help you with?")
    reprompt_text = "What can I help you with?"
    should_end_session = False
    return build_response(
        attributes,
        build_speechlet_response_without_card(speech_output, reprompt_text, should_end_session)
    )


def handle_finish_session_request(intent, session):
    """End the session with a message if the user wants to quit the game."""
    attributes = session['attributes']
    reprompt_text = ""
    speech_output = ("Player 1 got {} points, and Player 2 got {} points. ".format(session['attributes']['score1'], session['attributes']['score2']) +
                             "Thank you for playing {} with Alexa!".format(SKILL_NAME))
    should_end_session = True
    return build_response(
        attributes,
        build_speechlet_response_without_card(speech_output, reprompt_text, should_end_session)
    )


def is_answer_slot_valid(intent):
    if 'Answer' in intent['slots'].keys() and 'value' in intent['slots']['Answer'].keys():
        return True
    else:
        return False


# --------------- Helpers that build all of the responses -----------------

def build_speechlet_response_without_card(output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }
def build_speechlet_response(title, output, reprompt_text, should_end_session):
    question_num = 1
    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': "<speak><prosody rate = '93%'>" + output + "</prosody></speak>"
        },
        'card': {
            'type': 'Simple',
            'title': "",
            'text': output,
            'content': reprompt_text
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'SSML',
                'ssml': "<speak><prosody rate = '93%'>" + reprompt_text + "</prosody></speak>"
            }
        },
        'shouldEndSession': should_end_session
    }

def build_response(attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': attributes,
        'response': speechlet_response
    }
    
QUESTIONS = [
    {"What do Harry and Dumbledore find in the cave, that they suspect is a Horcrux?": ["locket"]},
    {"How many years after the Battle of Hogwarts does Harry's son, Albus Severus, go to Hogwarts for the first time?": ["19"]},
    {"What spell makes objects fly?": ["Wingardium Leviosa"]},
    {"What object in the Weasleys' house shows the location and status of each family member?": ["clock"]},
    {"Which Ministry of Magic employee expels Harry after the Dementor attack in the underpass?": ["Mafalda Hopkirk", "Hopkirk"]},
    {"What is Hermione's cat's name?": ["Crookshanks"]},
    {"What spell does Ron use to knock out the troll in the girls' bathroom?": ["Wingardium Leviosa"]},
    {"On his search for Rowena Ravenclaw's diadem, Harry speaks with which ghost?": ["Gray Lady", "Helena", "Helena Ravenclaw"]},
    {"What does the Knight Bus have instead of seats?": ["beds", "four-poster beds"]},
    {"Who finds Harry and Dudley in the underpass after the Dementor attack?": ["Mrs. Figg", "Arabella Figg", "Figg"]},
    {"According to legend, what is inside the Chamber of Secrets?": ["monster", "a monster"]},
    {"Through which ghost, does Justin Finch-Fletchley see the Basilisk.": ["Nearly Headless Nick", "Nick"]},
    {"In which part of Hogwarts does the troll find Hermione?": ["girls' bathroom", "bathroom"]},
    {"What does Dumbledore cast around the Goblet of Fire to prevent younger students from entering the Triwizard Tournament?": ["Age Line"]},
    {"From whose office do Fred and George first get the Marauder's Map?": ["Filch"]},
    {"What fiendish creatures are seen in the Room of Requirement, when Harry is searching for the diadem of Ravenclaw? A: Cornish pixies, B: grin-dee-lows, C: Gnomes": ["A: Cornish pixies", "A", "Cornish pixies"]},
    {"What object in the Department of Mysteries is Voldemort after?": ["prophecy"]},
    {"After Dumbledore's death, who becomes Headmaster of Hogwarts?": ["Severus Snape", "Snape", "Severus", "Professor Snape"]},
    {"What is the incantation for the Body-Bind Curse?": ["Petrificus Totalus"]},
    {"What do Harry and Dumbledore find in the cave, that they suspect is a Horcrux?": ["Locket"]},
    {"How many years after the Battle of Hogwarts does Harry's son, Albus Severus, go to Hogwarts for the first time?": ["19"]},
    {"What spell makes objects fly?": ["Wingardium Leviosa"]},
    {"What object in the Weasleys' house shows the location and status of each family member?": ["clock"]},
    {"Which Ministry of Magic employee expels Harry after the Dementor attack in the underpass?": ["Hopkirk", "Mafalda Hopkirk"]},
    {"What is Hermione's cat's name?": ["Crookshanks"]},
    {"What spell does Ron use to knock out the troll in the girls' bathroom?": ["Wingardium Leviosa"]},
    {"Where does Dumbledore first meet Tom Riddle?": ["orphanage"]},
    {"On his search for Rowena Ravenclaw's diadem, Harry speaks with which ghost?": ["The Grey Lady", "Grey Lady", "Helena Ravenclaw"]},
    {"What does the Knight Bus have instead of seats?": ["beds", "four-poster beds"]},
    # {"Who finds Harry and Dudley in the underpass after the Dementor attack?": ["Mrs. Figg", "Arabella Figg"]},
    {"According to legend, what is inside the Chamber of Secrets?": ["monster"]},
    {"In which part of Hogwarts does the troll find Hermione?": ["girls' bathroom", "bathroom"]},
    {"What does Dumbledore cast around the Goblet of Fire to prevent younger students from entering the Triwizard Tournament?": ["Age Line"]},
    {"From whose office do Fred and George first get the Marauder's Map?": ["Filch"]},
    {"After Dumbledore's death, who becomes Headmaster of Hogwarts?": ["Severus Snape", "Snape"]},
    {"What is the incantation for the Body-Bind Curse?": ["Petrificus Totalus"]},
    {"What does Dumbledore send to Harry with his phoenix in the Chamber of Secrets?": ["Sorting Hat"]},
    {"What is the name of the driver of the Knight Bus?": ["Ernie", "Ernie Prang"]},
    {"Who throws the knife that kills Dobby?": ["Bellatrix", "Bellatrix Lestrange"]},
    {"Whose body is Voldemort possessing when Harry meets him for the first time?": ["Quirrell"]},
    {"According to legend, who built the Chamber of Secrets?": ["Salazar Slytherin", "Slytherin"]},
    {"When they travel back in time, what spell do Harry and Hermione see Lupin use to calm the Whomping Willow?": ["Immobilus"]},
    {"What selects the champions who participate in the Triward Tournament?": ["Goblet of Fire"]},
    {"How many years did Sirius Black spend in Azkaban?": ["12"]},
    {"What type of creature grabs Harry's hand when he tries to take water from the lake in the Horcrux cave?": ["Inferi"]},
    {"What is used to destroy the Horcrux cup?": ["Basilisk fang", "Basilisk tooth", "fang", "tooth"]},
    {"After Ron eats a box of chocolates laced with love potion, Harry takes him to which professor?": ["Slughorn"]},
    {"What part of his body does Harry break at a Quidditch match in the second book?": ["arm"]},
    {"What object does Dumbledore use to revisit memories?": ["Pensieve"]},
    {"How many brothers does Ron have?": ["5"]},
    {"What item of clothing frees Dobby?": ["sock", "Harry's sock"]},
    {"According to Sirius Black, which member of Durmstrang is a former Death Eater?": ["Karkaroff", "Igor Karkaroff"]},
    {"How old is Harry when Snape finally gets to teach Defense Against the Dark Arts?": ["16"]},
    {"Who does the Daily Prophet call 'Undesirable Number One'?": ["Harry", "Harry Potter"]},
    {"What is the name of Gilderoy Lockhart's autobiography?": ["Magical Me"]},
    {"Harry practices the Patronus Charm on what type of creature in Professor Lupin's office?": ["boggart"]},
    {"When Harry sees Karkaroff's trial through the Pensieve, Karkaroff offers up the names of Rosier, Rookwood, Snape, and, which other Death Eater?": ["Barty Crouch Junior"]},
    {"What does O.W.L. stand for?": ["Ordinary Wizarding Levels"]},
    {"What rescues Harry, Ron, and Fang, from the acromantulas in the Forbidden Forest?": ["car", "flying car", "Ford Anglia"]},
    {"What is Lupin's middle initial?": ["J"]},
    {"What type of animal carries post and packages in the wizarding world?": ["owl"]},
    {"Which student is thought to have been taken by the monster into the Chamber of Secrets?": ["Ginny", "Ginny Weasley"]},
    {"What subject does Professor Grubbly-Plank teach in Harry's fifth year?": ["Care of Magical Creatures"]},
    {"How many types of balls are used to play Quidditch?": ["three"]},
    {"What is Madame Maxime's first name?": ["Olympe"]},
    {"What creature tries to attack Harry, Ron, and Hermione, outside of the Shrieking Shack?": ["werewolf", "Lupin"]},
    {"What is coming out of the skull's mouth in the dark mark?": ["snake", "serpent"]},
    {"What phrase is cut into Harry's hand during his detention with Professor Umbridge?": ["I must not tell lies"]},
    {"What book does Hermione take from the library to make Polyjuice Potion?": ["Most Potent Potions"]},
    {"What is the core of Harry's wand?": ["phoenix feather", "phoenix tail feather", "Fawkes feather"]},
    {"When Professor Trelawney predicts 'servant and master shall be reunited once more', she is referring to which servant?": ["Peter Pettigrew", "Pettigrew", "Wormtail"]},
    {"What creature does Mad-Eye Moody use to teach the unforgivable curses?": ["spider"]},
    {"Who kills Professor Dumbledore?": ["Snape", "Severus Snape"]},
    # {"What time does the Hogwarts Express leave King's Cross Station on the first day of term?": ["11 A M", "11"]},
    {"Which spell produces light from the end of a wand?": ["Lumos"]},
    {"Who is the headmistress of Beauxbatons Academy of Magic?": ["Madame Maxime"]},
    {"What is the name of the Black family house elf?": ["Kreacher"]},
    {"What poisoned drink does Ron have in Professor Slughorn's office?": ["mead", "oak matured mead"]},
    {"Which ghost appears at the first start-of-term feast with a sword?": ["Bloody Baron"]},
    {"What is the incantation to create fire?": ["Incendio"]},
    {"What does Professor Lupin give Harry to eat after the Dementor attack on the Hogwarts Express?": ["chocolate", "chocolate bar"]},
    {"Who does Tonks marry?": ["Lupin", "Remus Lupin"]},
    {"What type of creature attacks Harry and Dudley in the underpass?": ["Dementor"]},
    {"Who signs a note left inside the fake locket Horcrux?": ["R A B", "Regulus Black", "Regulus Arcturus Black"]},
    {"Who teaches flying lessons at Hogwarts?": ["Madam Hooch"]},
    {"How many turns does Dumbledore suggest giving the Time Turner to go back and save Sirius?": ["3"]},
    {"What is Hagrid's half-brother's name?": ["Grawp"]},
    {"Who sets Hagrid's hut on fire after Dumbledore has been killed?": ["Bellatrix Lestrange", "Bellatrix"]},
    {"Which class does Hermione storm, out of, in her third year at Hogwarts?": ["Divination"]},
    {"What is the make and model of the Weasleys' flying car?": ["Ford Anglia"]},
    {"Who is the only one of the three brothers from 'The Tale of the Three Brothers' to voluntarily present himself to Death during old age?": ["third", "youngest", "Ignotus"]},
    {"What is the name of Ron's pet rat?": ["Scabbers"]},
    {"Where in Hogwarts is the Ravenclaw diadem Horcrux hidden?": ["Room of Requirement"]},
    {"Which position does Ron Weasley play on the Gryffindor Quidditch team?": ["Keeper"]},
    {"What does Rita Skeeter use to write her interviews?": ["Quick Quotes Quill"]},
    {"Which of Ron's brothers marries Fleur Delacour?": ["Bill"]},
    {"What is the name of Harry's owl?": ["Hedwig"]},
    {"Who destroys the diadem Horcrux?": ["Harry"]},
    {"Which school textbook is property of the Half-Blood Prince?": ["Advanced Potion Making"]},
    {"What is the wrist movement that accompanies the Levitation Charm?": ["swish and flick"]},
    {"What do the Weasley twins use to eavesdrop on meetings at 12 Grimmauld Place?": ["extendable ear"]},
    {"After Dumbledore's death, who writes an unoffical autobiography on him?": ["Rita Skeeter"]},
    {"What type of creature is Aragog?": ["acromantula"]},
    {"Which Horcrux was created last?": ["Nagini", "snake"]},
    {"What is Ron Weasley's middle name?": ["Bilius"]},
    {"Who is Hagrid, burying when Professor Slughorn and Harry pay him a visit?": ["Aragog"]},
    {"Which Hogwarts professor is levitated above a table while Lord Voldemort meets with his Death Eaters?": ["Charity Burbage", "Muggle Studies"]},
    {"What spell does Hermione use to fix Harry's glasses?": ["Oculus Reparo"]},
    {"What is Grindelwald's first name?": ["Gellert"]},
    {"What does Ron put on the feet of his spider Boggart to make it funny?": ["roller skates"]},
    {"In the dungeons of which house are Harry and his friends imprisoned after being captured by the Snatchers?": ["Malfoy Manor", "Malfoy"]},
    {"What is the first name of Hogwarts founder Ravenclaw?": ["Rowena"]},
    {"In which school year does Harry use the textbook Advanced Potion Making?": ["six", "sixth"]},
    {"Whose home do Harry and Hermione visit in Godric's Hollow?": ["Bathilda Bagshot", "Potter", "parents"]},
    {"What two creatures does Voldemort use in the Battle of Hogwarts aside from Dementors?": ["giants and acromantulas", "acromantulas and giants"]},
    {"Who casts the Dark Mark over Hogwarts once Dumbledore has been killed?": ["Bellatrix", "Bellatrix Lestrange"]},
    {"Which student is approached by the snake that Malfoy conjures during the Duelling Club?": ["Justin", "Justin Finch-Fletchley"]},
    {"What does the spell, Morsmordre, produce?": ["Dark Mark"]},
    {"What means of transportation do Harry and Hagrid use during their escape from Privet Drive?": ["flying motorcycle", "flying motorbike"]},
    {"What is Mad-Eye Moody's first name?": ["Alastor"]},
    {"What is the name of the invisible creatures that Luna claims float into your ears and make your brain go fuzzy?": ["wrackspurt"]},
    {"How does Harry destroy Tom Riddle's diary?": ["Basilisk fang", "fang"]},
    {"Which schoolmate do Harry and Ron find imprisoned in the dungeons at Malfoy Manor?": ["Luna Lovegood", "Luna"]},
    {"What is the name for the most powerful love potion in the world?": ["Amortentia"]},
    {"Who became master of the Elder Wand after Grindelwald?": ["Dumbledore"]},
    {"How many times has Gilderoy Lockhart won Witch Weekly's Most-Charming-Smile award?": ["5"]},
    {"What does Madame Maxime tell Hagrid that her horses drink?": ["single malt whiskey", "whiskey"]},
    {"Which Horcrux does Harry find in Bella tricks's vault?": ["cup", "Hufflepuff's cup", "Helga Hufflepuff's cup", "chalice"]},
    {"Which Ministry official does Harry transform into using Polyjuice Potion in order to sneak into the Ministry of Magic?": ["Albert Runcorn", "Runcorn"]},
    {"The Marauder's Map was created by Wormtail, Padfoot, Prongs, and?": ["Moony"]},
    {"What is Nicolas Flamel's profession?": ["alchemist"]},
    {"What from does Snape's patronus take?": ["doe"]},
    {"Who stole the locket Horcrux from the Black house after Sirius' death?": ["Mundungus Fletcher"]},
    {"On which night is the Yule Ball held at Hogwarts?": ["Christmas Eve"]},
    {"What is the incantation for the spell that severs items and cuts through things?": ["Diffindo"]},
    {"What is the name of a red letter that carries an angry message?": ["Howler"]},
    {"What are Dark wizard catchers called?": ["Aurors"]},
    {"Who does Kingsley Shacklebolt act as a bodyguard for?": ["Muggle prime minister"]},
    {"What does a house elf's master have to present them with to free them?": ["clothes"]},
    {"Who is Cho Chang's date to the Yule Ball?": ["Cedric", "Cedric Diggory"]},
    {"What is Felix Felicis also known as?": ["liquid luck"]},
    {"With whom was Snape in love?": ["Lily", "Lily Potter"]},
    {"Which creatures does Professor Lockhart introduce as part of his first Defense Against the Dark Arts lesson?": ["Cornish pixies"]},
    # {"Who is Narcissa Malfoy's sibling?": ["Bellatrix", "Bellatrix Lestrange"]},
    {"What is Krum's first name?": ["Viktor"]},
    # {"Who opened the Chamber of Secrets 50 years before Harry's second year at Hogwarts?": ["Tom Riddle", "Voldemort"]},
    {"Which of these is not an unforgivable curse? A: Imperio, B: Crucio, C: Sectumsempra": ["C: Sectumsempra", "Sectumsempra", "C"]},
    {"How are Sirius Black and Bella tricks Lestrange related?": ["cousins"]},
    {"What form did Lily Potter's Patronus take?": ["doe"]},
    {"Who is chosen by Voldemort to kill Dumbledore?": ["Draco Malfoy", "Malfoy", "Draco"]},
    {"Which potion do the students have to brew to win a vial of Felix Felicis?": ["Draught of Living Death"]},
    {"What is Greg-or-ovitch's profession?": ["wand maker"]},
    {"How old was Tom Riddle when he first opened the Chamber of Secrets?": ["16"]},
    {"When Professor Snape takes over Lupin's Defense Against the Dark Arts lesson, he teaches the class about what type of creature?": ["werewolf"]},
    {"What is the incantation for the spell that causes an object to grow larger?": ["Engorgio"]},
    {"What is the full name of Harry's second son?": ["Albus Severus Potter"]},
    {"Which Death Eater's trial does Harry see when he first looks into Dumbledore's Pensieve?": ["Igor Karkaroff", "Karkaroff"]},
    {"What subject does Professor Slughorn teach?": ["potions"]},
    # {"Who retrieves the sword of Gryffindor from the lake?": ["Harry"]},
    {"Gwenog Jones is the captain of which Quidditch team?": ["Holyhead Harpies", "Harpies"]},
    {"What creature does Harry see in the shadows just before the Knight Bus arrives?": ["dog", "the Grim", "Sirius Black", "Sirius", "black dog", "Grim"]},
    {"What is Tom Riddle's middle name?": ["Marvolo"]},
    {"What object has the power to destroy Horcruxes because it imbibed Basilisk venom in the Chamber of Secrets?": ["sword of Gryffindor"]},
    {"Who is the Minister for Magic after Cornelius Fudge?": ["Rufus Scrimgeour", "Scrimgeour"]},
    {"What type of dragon does Cedric face in the first task of the Triwizard Tournament?": ["Swedish short snout"]},
    {"Which Hogwarts student was killed by the Basilisk?": ["Moaning Myrtle", "Myrtle"]},
    {"Which subject does Professor Umbridge teach at Hogwarts?": ["Defense Against the Dark Arts"]},
    {"How many Unforgivable Curses are there?": ["3"]},
    {"What object has a flesh memory?": ["Snitch", "Golden Snitch"]},
    {"Who is the Half-Blood Prince?": ["Severus Snape", "Snape", "Professor Snape"]},
    {"What is the secret to calming Fluffy?": ["music", "play music", "playing music"]},
    {"What is Professor Flitwick's first name?": ["Filius"]},
    {"Who vomits slugs when his spell accidentally backfires?": ["Ron"]},
    {"Who saves Harry from drowning in the frozen lake in the Forest of Dean?": ["Ron"]},
    {"What creatures are brought from Romania for the first task of the Triwizard Tournament?": ["dragons"]},
    {"In which country does Charlie Weasley study dragons?": ["Romania"]},
    {"Who kills Cedric Diggory on Voldemort's orders?": ["Wormtail", "Peter Pettigrew", "Pettigrew", "Peter"]},
    {"Who creates the Slug Club?": ["Slughorn", "Professor Slughorn"]},
    # {"Who instructs the Hogwarts suits of armor to defend the castle during the Battle of Hogwarts?": ["McGonagall", "Professor McGonagall", "Magonagal"]},
    {"What is Dumbledore's full name?": ["Albus Percival Wulfric Brian Dumbledore"]},
    {"Which creature threatens Harry, Ron, and Hermione, at Gringotts?": ["dragon"]},
    {"Which Quidditch player does Ron have a model of?": ["Krum", "Viktor Krum"]},
    {"When Harry opens the locket Horcrux, whose voice taunts Ron?": ["Voldemort"]},
    {"How many large tables run the length of the Great Hall at Hogwarts?": ["4"]},
    {"What is the incantation for the charm that repels a Boggart?": ["Riddikulus"]},
    {"What is Hermione's middle name?": ["Jean"]},
    {"Which of Hagrid's pets was sent to Romania with Charlie Weasley's friends?": ["Norbert"]},
    {"What is the name of the bandits who work for the Death Eaters once they are in control of the Ministry?": ["Snatchers"]},
    {"Who was the headmaster of Hogwarts when the Chamber of Secrets was first opened?": ["Professor Dippet", "Armando Dippet", "Dippet"]},
    {"What is the name of the effect that happens when twin wand cores duel?": ["Priori Incantatum"]},
    {"Harry first Apparates alongside whom?": ["Dumbledore"]},
    {"Who are the Dementors looking for when they board the Hogwarts Express?": ["Sirius", "Black", "Sirius Black"]},
    {"What does Draco Malfoy use to get the Death Eaters into Hogwarts?": ["Vanishing Cabinet"]},
    {"What legendary event is hosted by Hogwarts during Harry's fourth year?": ["Triwizard Tournament"]},
    {"According to Griphook, who put the fake sword of Gryffindor inside Bella tricks Lestrange's vault?": ["Snape", "Professor Snape", "Severus Snape"]},
    {"Professor Moody turns Draco Malfoy into what type of animal?": ["ferret"]},
    {"Where do Harry and Dumbledore go to find a Horcrux together?": ["cave"]},
    {"What spell performed by Harry is the cause of his disciplinary hearing in the Ministry of Magic?": ["Patronus Charm", "Expecto Patronum"]},
    {"What item does Dumbledore bequeath to Hermione?": ["Tales of Beedle the Bard"]},
    {"Sybil Trelawney's first prophecy speaks of a boy born at the end of which month?": ["July"]},
    {"Which Committee in the Ministry of Magic sentences Buckbeak to death?": ["Disposal of Dangerous Creatures"]},
    {"Who does Voldemort think the Elder Wand belongs to after he realizes it doesn't belong to Dumbledore?": ["Snape", "Severus Snape", "Professor Snape"]},
    {"What is the incantation for the memory charm that backfires on Professor Lockhart in the Chamber of Secrets?": ["Obliviate"]},
    {"Which item is not one of the Deathly Hallows? A: Mirror of Erised, B: Elder Wand, C: Ressurection Stone": ["A: Mirror of Erised", "Mirror of Erised", "A"]},
    {"What department in the Ministry of Magic does Barty Crouch head up when the Triwizard Tournament occurs?": ["Department of International Magical Cooperation", "International Magical Cooperation"]},
    {"Who gives Harry the Gillyweed in the book?": ["Dobby"]},
    {"Who gives Harry the Gillyweed in the movie?": ["Neville Longbottom", "Neville"]},
    {"What is the incantation for the stunning spell?": ["Stupefy"]},
    {"Which school does Krum attend?": ["Durmstrang"]},
    {"For which national Quidditch team does Krum play?": ["Bulgaria"]},
    {"What is the name of the Weasleys' old owl?": ["Errol"]},
    {"Who is the Keeper of Keys and Grounds at Hogwarts?": ["Hagrid", "Rubeus Hagrid"]},
    {"Which dragon does Fleur Delacour face in the first task of the Triwizard Tournament?": ["Welsh green"]},
    {"According to Dumbledore, what Horcrux did Voldemort create unintentionally?": ["Harry", "Harry Potter", "Potter"]},
    {"In the first book, into which house is the first student sorted?": ["Hufflepuff"]},
    # {"Who was the last person to be sorted before Harry?": ["Sally-Anne Perks", "Perks", "Sally-Anne"]},
    {"What gift did Percy get from his parents when he became Prefect?": ["owl", "Hermes"]},
    {"Who was the Care of Magical Creatures teacher before Hagrid?": ["Kettleburn", "Professor Kettleburn"]},
    {"What is the lowest grade available on standardized wizarding tests?": ["Troll"]},
    {"In Prisoner of Azkaban, Harry stays at the Leaky Cauldron and receives help on his History of Magic homework from which shopkeeper?": ["Florean Fortescue", "Fortescue"]},
    {"Who wins the Quidditch World Cup in Goblet of Fire?": ["Ireland", "Irish"]},
    {"Which type of candy did Romilda Vane spike with love potion?": ["chocolate cauldrons"]},
    {"What is the name of Filch's cat?": ["Mrs. Norris"]},
    {"Where did the Weasleys spend the summer before Ron's third year at Hogwarts?": ["Egypt"]},
    {"During one memorable Care of Magical Creatures lesson, the students search for leprechaun gold with the aid of what magical creature?": ["Niff-ler", "Niffler", "Nifflers", "Niff-lers"]},
    {"Hermione takes this elective course with Professor Babbling.": ["Study of Ancient Runes", "Ancient Runes"]},
    {"Hagrid created Blast-Ended Skrewts by breeding a Manticore with which other magical creature?": ["Fire crab"]},
    {"Molly Weasley lost two brothers in the First Wizarding War. One was named Fabian. What was the other's name?": ["Gideon"]},
    {"What was Molly Weasley's maiden name?": ["Prewett"]},
    {"What is Fleur Delacour's younger sister's name?": ["Gabrielle"]},
    {"What is Dolores Umbridge's favorite color?": ["pink"]},
    {"What is the name of the guest that the Dursleys are entertaining on the night of Harry's twelfth birthday?": ["Mr. Mason", "Mason"]},
    {"What is the first, D, of the three, D's, of Apparition?": ["destination"]},
    {"What is Cho Chang's Patronus?": ["swan"]},
    {"What is Kingsley Shacklebolt's Patronus?": ["lynx"]},
    {"What does Ginny name her pet pygmy puff?": ["Arnold"]},
    {"What beverage should you offer to a narl in order to tell if it is a narl and not a hedgehog?": ["milk"]},
    {"What is the full name of Gryffindor's house ghost?": ["Sir Nicholas de Mimsy Porpington"]},
    {"Who does Hermione claim to be, when she, Ron, and Harry, are captured by Snatchers?": ["Penelope", "Penelope Clearwater"]},
    {"What does S. P. E. W. stand for?": ["Society for the Promotion of Elvish Welfare"]},
    {"Which musical artist does Molly Weasley like to listen to on the radio?": ["Celestina Warbeck"]},
    {"In his first flying lesson, what does Harry dive to catch?": ["Remembrall", "Neville's Remembrall"]},
    {"What was Sirius's Marauder nickname?": ["Padfoot"]},
    {"What was James's Marauder nickname?": ["Prongs"]},
    {"What was Peter's Marauder nickname?": ["Wormtail"]},
    {"What was Remus's Marauder nickname?": ["Moony"]},
    {"What is the incantation to open a lock?": ["Alohomora"]},
    {"What is Bella tricks Lestrange's husband's name?": ["Rodolphus"]},
    {"What is Narcissa Malfoy's maiden name?": ["Black"]},
    {"What was Voldemort's mother's name?": ["Merope", "Merope Gaunt"]},
    {"In Chamber of Secrets, which professor mistakenly refers to Hermione as Miss Grant?": ["Professor Binns", "Binns"]},
    {"After Oliver Wood graduates from Hogwarts, who is made captain of the Gryffindor Quidditch team?": ["Angelina Johnson", "Angelina"]},
    {"How many Outstandings does Harry receive on his O.W.L.s? ": ["1"]},
    {"How many Sickles are in a Galleon?": ["17"]},
    {"How many Knuts are in a Sickle?": ["29"]},
    {"Who gives Head-wig to Harry?": ["Hagrid"]},
    {"How many years before Harry's second year at Hogwarts was Nearly Headless Nick killed?": ["500"]},
    {"What color is Hagrid's umbrella?": ["pink"]},
    {"In her singing Valentine to Harry in Chamber of Secrets, Ginny compares Harry's eyes to 'fresh pickled, toads' and his hair to what?": ["blackboard"]},
    {"What is the name of the joke shop in Hogsmeade?": ["Zonko's"]},
    {"Hermione alters which common item to communicate meeting times to members of Dumbledore's Army?": ["galleons"]},
    {"What creature has a cry that is fatal to anyone who hears it?": ["mandrake"]},
    {"How many inches long is Harry's wand?": ["11"]},
    {"Who does Hermione attend the Slug Club Christmas party with?": ["Cormac", "McLaggen", "Cormac McLaggen"]},
    {"In Goblet of Fire, who is the head of the Department of Magical Games and Sports?": ["Bagman", "Ludo Bagman"]},
    {"What is the name of the man who is supposed to execute Buckbeak?": ["Macnair"]},
    {"What is the name of the prep school Dudley Dursley starts attending in the Sorceror's Stone?": ["Smeltings"]},
    {"What is Horace Slughorn's favorite candy?": ["crystallized pineapple", "pineapple"]},
    {"What does Vernon Dursley's company sell?": ["drills"]},
    {"After Marietta Edgecombe betrays Dumbledore's Army, what word is cursed across her face?": ["Sneak"]},
    {"What is the name of Dudley's best friend, who goes to the zoo with Harry and the Dursleys at the beginning of the series?": ["Piers Polkiss", "Piers"]},
    {"How many bottles are part of the logic puzzle at the end of Sorcerer's Stone?": ["7"]},
    {"What did James and Sirius call Snape during their time at Hogwarts?": ["Snivellus"]},
    {"What color was Tonks's hair when Harry first met her?": ["purple", "violet"]},
    {"What is Tonks's first name?": ["Nymphadora"]},
    {"Who sends Aunt Petunia a Howler?": ["Dumbledore"]},
    {"What were the Buglarian National Quidditch team mascots?": ["Veela"]},
    {"Which wandmaker made Viktor Krum's wand?": ["Gregorovitch"]},
    {"In Half-Blood Prince, Harry learns that Buckbeak has to be renamed to evade Ministry suspicion. What is his new name?": ["Witherwings"]},
    {"Who is Ginny's first boyfriend?": ["Michael Corner"]},
    {"Who gives Harry a pocket sneakoscope for his thirteenth birthday?": ["Ron"]},
    {"Who gives Harry a broomstick servicing kit for his thirteenth birthday?": ["Hermione"]},
    {"What magical creature lures people into bogs?": ["Hinkypunks"]},
    {"How old is Harry when he first wins the Quidditch Cup?": ["13"]},
    {"Who does Harry take to the Slug Club Christmas party?": ["Luna", "Luna Lovegood"]},
    {"What is the name of the three-headed dog that guards the Sorcerer's Stone?": ["Fluffy"]},
    {"What does Ron give Hermione for Christmas in Order of the Phoenix?": ["perfume"]},
    {"What color is the Sorcerer's Stone?": ["red"]},
    {"Outside which village is the old Riddle House located?": ["Little Hangleton"]},
    {"What is the name of the caretaker at the old Riddle House?": ["Frank", "Frank Bryce"]},
    {"What is the incantation for a tickling charm?": ["Rictusempra"]},
    {"What is inside the Golden Snitch that Dumbledore leaves to Harry?": ["resurrection stone"]},
    {"What did Hagrid give Harry for Christmas during his first year at Hogwarts?": ["flute"]},
    {"How many people in Harry's Care of Magical Creatures class could see the thestrals Hagrid showed them?": ["3"]},
    {"What magical creature was in Lupin's office when Harry went in for the first time?": ["grindylow"]},
    {"Who is the Hufflepuff ghost?": ["Fat Friar"]},
    {"Who is the bartender at the Three Broomsticks?": ["Madame Rosemerta"]},
    {"At which bar is Aberforth Dumbledore the bartender?": ["Hog's Head", "Hogs Head"]},
    {"Fred and George's birthday falls on which holiday?": ["April Fools"]},
    {"Who was the male Hufflepuff prefect from Harry's year?": ["Ernie", "Ernie MacMillan"]},
    {"Who was the female Hufflepuff prefect from Harry's year?": ["Hannah Abbot"]},
    {"Who was the male Slytherin prefect from Harry's year?": ["Draco Malfoy", "Draco", "Malfoy"]},
    {"Who was the female Slytherin prefect from Harry's year?": ["Pansy", "Pansy Parkinson"]},
    {"Who was the male Ravenclaw prefect from Harry's year?": ["Anthony Goldstein"]},
    {"Who was the female Ravenclaw prefect from Harry's year?": ["Padma Patil"]},
    {"Who was the male Gryffindor prefect from Harry's year?": ["Ron", "Ron Weasley"]},
    {"Who was the female Gryffindor prefect from Harry's year?": ["Hermione", "Hermione Granger"]},
    {"What was the name of the shop where Hermione purchased Crookshanks?": ["Magical Menagerie"]},
    {"What is Madam Pomfrey's first name?": ["Poppy"]},
    {"What is the password that Cedric tells Harry to use for the prefects' bathroom?": ["Pinefresh"]},
    {"What is Ginny's preferred Quidditch position?": ["Chaser"]},
    {"The Hogwarts motto is Draco Dormy-ens Nunquam Titillandus. What does this translate to?": ["never tickle a sleeping dragon"]},
    {"What color are Lockhart's robes when Harry first meets him?": ["forget-me-not-blue", "blue"]},
    {"A basilisk is created by hatching a hen's egg under what animal?": ["toad"]},
    {"Who was the first person to escape from Azkaban?": ["Barty Crouch Junior"]},
    {"What was the name of Vernon Dursley's company?": ["Grunnings"]},
    {"What is Severus Snape's mother's first and last name?": ["Eileen Prince"]},
    {"Which Weasley had a penpal who attended the Wizarding school in Brazil?": ["Bill"]},
    {"What is Gilderoy Lockhart's favorite color? Lilac": [""]},
    {"Which Unforgivable Curse did Harry never cast in the books?": ["Avada Kedavra", "Killing Curse"]},
    {"What was the name of Lavender Brown's pet rabbit, who dies in the third book?": ["Binky"]},
    {"A bezoar is found in the stomach of which animal?": ["goat"]},
    {"What does Ron buy from the Magical Menagerie in the third book?": ["rat tonic", "rat medicine"]},
    {"Who was the first person sorted in the first book?": ["Hannah Abbot"]},
    {"What kind of being is Peeves?": ["poltergeist"]},
    {"What shape is the Gryffindor boys' dormitory?": ["circle", "circular", "round"]},
    {"What color is Crookshanks?": ["ginger", "red", "orange"]},
    {"Dumbledore has a scar above his left knee that is a perfect map of what?": ["London Underground"]},
    {"What is the Potters' vault number in Gringotts?": ["687"]},
    {"Can squibs see dementors?": ["no"]},
    {"According to the Marauders Map, what is the correct order of the Marauders?": ["Moony Wormtail Padfoot and Prongs"]},
    {"What flavor ice lolly did the Dursleys buy Harry at the zoo?": ["lemon"]},
    {"What kind of fruit do you have to tickle to gain entry to the Hogwarts kitchen?": ["pear"]},
    {"Who watches Harry from the bushes on his twelfth birthday?": ["Dobby"]},
    {"What vault at Gringotts is the Sorcerer's Stone in?": ["713"]},
    {"The pus of what plant is used to cure stubborn acne?": ["bubotuber"]},
    {"Name one of the three Irish Chasers in the 1994 World Cup": ["Troy", "Mullet", "Moran"]},
    {"Which magical creature is also known as a living shroud?": ["lethifold"]},
    {"What house was Lockhart, in when he was at Hogwarts?": ["Ravenclaw"]},
    {"What percent Veela is Fleur Delacour?": ["25", "one-fourth", "one quarter", "25 percent"]},
    {"How many characters, including ghosts and animals, were petrified by the Basilisk?": ["6"]},
    {"Ginny was the first female born to the Weasley family in how many generations?": ["7"]},
    {"For which professional Quidditch team does Oliver Wood play after he graduates?": ["Puddlemere United"]},
    {"What is the name of the man who looks after Aunt Marge's dogs while she is visiting her brother?": ["Colonel Fubster"]},
    {"Where did Harry come across the name Head-wig?": ["History of Magic"]},
    {"Who is driving the flying car when the Weasleys rescue Harry from Privet Drive in the second book?": ["Fred"]},
    {"What is the name of the Wizarding childrens' game similar to marbles?": ["gobstones"]},
    {"Which Hufflepuff student gets petrified by the basilisk?": ["Justin", "Justin Finch-Fletchley"]},
    {"What magical creature is similar to a fairy, except for an extra pair of arms and legs, body hair, and sharp, venemous teeth?": ["doxy", "doxies"]},
    {"What is Ron's favorite Quidditch team?": ["Chudley Cannons"]},
    {"What color are the Chudley Cannons' robes?": ["orange"]},
    {"What item of Ron's was turned into a spider by Fred when he was a little kid, giving him his fear of spiders?": ["teddy bear"]},
    {"Fred and George's pygmy puffs are miniature versions of which other magical creature?": ["puffskein"]},
    {"What does the Boggart turn into for Seamus Finnegan?": ["banshee"]},
    {"What does N.E.W.T. stand for?": ["Nastily Exhausting Wizarding Test"]},
    {"What was Hagrid's pet dragon's name?": ["Norbert"]},
    {"What form does the Boggart turn into for Parvati?": ["mummy"]},
    {"What color were Hermione's dress robes for the Yule Ball?": ["periwinkle", "blue", "light blue"]},
    {"What is Harry's middle name?": ["James"]},
    {"Luna can see thestrals because she saw this person die": ["her mother", "mother", "mom", "her mom"]},
    {"What kind of creature does Harry help the Weasley brothers throw over the garden wall in the second book?": ["gnomes", "gnome"]},
    {"Who is oldest: Harry, Ron, or Hermione?": ["Hermione"]},
    {"Who is youngest: Harry, Ron, or Hermione?": ["Harry"]},
    {"Which beverage does Winky get drunk off of?": ["butter beer", "butterbeer"]},
    {"What is the core of Fleur's wand?": ["veela hair"]},
    {"What potion does Snape brew for Lupin in Prisoner of Azkaban?": ["wolfsbane"]},
    {"What is the address of Sirius's house?": ["12 Grimmauld Place"]},
    {"Where did Harry take Cho Chang on a disastrous date?": ["Madam Puddifoot's"]},
    {"Which ball are Beaters concerned with in a Quidditch game?": ["bludger"]},
    {"How many bludgers are there in a regulation, Qudditch game?": ["2"]},
    {"How many Chasers play on a team?": ["3"]},
    {"What, wood, is Harry's wand made of?": ["holly"]},
    {"Who wrote Fantastic Beasts and Where to Find Them?": ["Newt Scamander"]},
    {"Which house did Newt Scamander belong to?": ["Hufflepuff"]},
    {"What is Rita Skeeter's animagus form?": ["beetle"]},
    {"What color were the flames that Hermione carried around in a jar in the first book?": ["blue"]},
    {"What form does Hermione's Patronus take?": ["otter"]},
    {"What was Lily Potter's maiden name?": ["Evans"]},
    {"What is Bella tricks and Nar-sis-uh's sister's name?": ["Andromeda"]},
    {"What was the first password to the Gryffindor common room in Harry's first year?": ["Caput draconis"]},
    {"What is the Slytherin common room password in Chamber of Secrets?": ["pureblood"]},
    # {"What day is Harry's birthday?": ["42947"]},
    {"What was the name of the forest where Harry, Ron, and Hermione, were taken by Snatchers?": ["Forest of Dean"]},
    {"In the book, where did the snake in the zoo say he was going to go? ": ["Brazil"]},
    {"How many ways are there to commit a foul in Quidditch? ": ["700"]},
    {"Which body part did Neville break in his first flying lesson?": ["wrist"]},
    {"Moaning Myrtle was hiding in the bathroom the night she died because Olive Hornby was making fun of her what?": ["glasses"]},
    {"What candy did Fred Weasley give to Dudley Dursley?": ["Ton Tongue Toffee"]},
    {"Who was the head of Ravenclaw House?": ["Professor Flitwick", "Flitwick"]},
    {"Who was the head of Slytherin House?": ["Professor Snape", "Snape"]},
    {"Who was the head of Hufflepuff House?": ["Professor Sprout", "Sprout"]},
    {"Who was the head of Gryffindor House?": ["Professor McGonagall", "McGonagall"]},
    {"Who was the Potters' secret keeper?": ["Peter Pettigrew", "Wormtail", "Pettigrew", "Peter"]},
    {"Who is the Hogwarts librarian?": ["Pince", "Irma Pince", "Madam Pince"]},
    {"Who are the last people to finish singing the school song at Harry's first Start of Term feast?": ["Fred and George", "George and Fred", "Weasley twins"]},
    {"What program did Argus Filch enroll in to learn magic?": ["Kwikspell"]},
    # {"What year is Oliver Wood when Harry is a first year?": ["fifth", "5"]},
    {"What potion does Umbridge threaten to use on Harry?": ["Veritaserum"]},
    {"Which of her features did Hermione have Madam Pomfrey shrink to less than their original size after Malfoy engorged them?": ["front teeth", "teeth"]},
    {"What do Hermione's parents work as?": ["dentists"]},
    {"What is the name of the wizard who mispronounced a spell and ended up with a buffalo on his chest?": ["Baruffio"]},
    {"Who is the author of the Standard Books of Spells?": ["Miranda Goshawk"]},
    {"What book does Hagrid have the students buy before Harry's third year?": ["Monster Book of Monsters"]},
    {"What page does Snape tell students to turn to when he is teaching Defense Against the Dark Arts in the third book?": ["394"]},
    {"Who wrote The Life and Lies of Albus Dumbledore?": ["Rita Skeeter"]},
    {"In which village did Bathilda Bagshot live?": ["Godric's Hollow"]},
    {"Which house is Parvati Patil's twin in?": ["Ravenclaw"]},
    {"Which of the dragons used during the Tri Wizard Tournament was the only one native to the British Isles?": ["Welsh Green"]},
    {"Which wizard bows to a young Harry Potter in a shop, years before he knows about magic?": ["Dedalus Diggle", "Diggle", "Dedalus"]},
    {"What do you have to dial on the phone to access the Ministry of Magic guest entrance?": ["6 2 4 4 2"]},
    {"Name one of the two Chocolate Frog cards Ron is missing on he and Harry's first trip to Hogwarts": ["Agrippa", "Ptolemy"]},
    {"Who was Fleur Delacour's date to the Yule Ball?": ["Roger Davies"]},
    # {"In which year was the Quidditch match in which all possible fouls occurred?": ["1473"]},
    {"What vegetable were the flesh-eating slugs ruining, prompting Hagrid to go to Knockturn Alley to buy poison?": ["cabbage", "cabbages"]},
    {"How many members of the Advance Guard came to pick Harry up from the Dursleys'?": ["9"]},
    {"Name the pixie-like creature considered a tree guardian and mostly found in, wand, trees": ["Bowtruckle"]},
    {"Against which house was Gryffindor playing the day Ron thought Harry dosed his pumpkin juice with Liquid Luck?": ["Slytherin"]},
    {"If someone is hit by the Furnunculus Curse and the Jelly-Legs Jinx at the same time, they grow tentacles all over which part of their body?": ["face"]},
    {"What is Dumbledore's favorite flavor of jam?": ["raspberry"]},
    {"What school was Harry set to attend before he received his Hogwarts letter?": ["Stonewall", "Stonewall High"]},
    {"What is the incantation for the spell that causes something to repel water?": ["Impervius"]},
    {"Who went by the callname River on Potterwatch?": ["Lee Jordan", "Lee"]},
    {"In addition to Harry and Neville, there was one other sixth year student attending the Slug Club meeting on the train. What house was this student in?": ["Slytherin"]},
    {"What type of gem does the sword of Gryffindor have on its handle?": ["rubies", "ruby"]},
    {"Who are the Weasleys visiting the summer before Ron's third year at Hogwarts?": ["Bill"]},
    {"How much was Mr. Weasley fined for bewitching the Ford Anglia?": ["50 Galleons", "50"]},
    {"What type of pet does Millicent Bulstrode have?": ["cat"]},
    {"Name the prison Grindelwald built to hold his enemies": ["Nurmengard"]},
    {"Who replaced the Fat Lady as guard to the Gryffindor Common Room after she was attacked by Sirius Black?": ["Sir Cadogan"]},
    {"Dumbledore wasn't at Hogwarts when Voldemort tried to steal the stone. He had received an urgent owl summoning him to which city?": ["London"]},
    {"Slughorn took the shape of what household object in an attempt to hide from Dumbledore?": ["armchair", "chair"]},
    {"A student from which house stumbled upon Harry near the petrified bodies of Justin and Nick?": ["Hufflepuff"]},
    {"True or false: the Polyjuice potion gave Hermione a tail": ["TRUE"]},
    {"What kind of tape did Ron use on his broken wand?": ["Spello tape", "spello"]},
    {"What type of animal did Uncle Vernon see reading a map on a street corner at the beginning of the series?": ["cat", "McGonagall"]},
    {"What is the incantation that increases the volume of the caster's voice?": ["Sonorus"]},
    {"What type of liquor is manufactured by Ogden's?": ["firewhiskey"]},
    {"What color is Cornelius Fudge's bowler hat?": ["lime green", "green"]},
    {"Who said, 'Never trust anything that can think for itself if you can't see where it keeps its brain'?": ["Arthur Weasley", "Mr. Weasley", "Arthur"]},
    {"Which potion is used as a treatment for colds but also leaves the drinker smoking at the ears for several hours afterwards?": ["pepperup potion", "pepperup"]},
    {"What murderous plant likes to strangle people but hates bright light?": ["Devil's Snare"]},
    {"What is the incantation for the spell that makes your wand behave like a compass?": ["Point Me"]},
    # {"How many staircases are there at Hogwarts? A: 42, B: 142, C: 242": ["B", "142", "B: 142"]},
    {"What did Harry tell Stan Shunpike his name was the first time they met?": ["Neville", "Neville Longbottom"]},
    {"What color are Quick Quotes Quills?": ["green", "acid green"]},
    {"True or false: In the books, Ron's first time into the forbidden forest occurred in his second year?": ["TRUE"]},
    {"What codename did Sirius Black go by while he was in hiding?": ["Snuffles"]},
    {"What trick Quidditch maneuver did Viktor Krum execute in the World Cup?": ["Wronski Feint"]},
    {"What type of magical creature was sentenced to death after savaging someone but later let off because everyone was too scared to go near it?": ["manticore"]},
    {"In the fourth book, Fred and George slipped, dung, from which type of creature, into Percy's, in, tray?": ["dragon"]},
    {"What was the cake that Molly made Harry for his 17th birthday shaped like?": ["Snitch"]},
    {"What is the name of the newspaper that Xenophilius Lovegood edits?": ["The Quibbler"]},
    {"Who was the bartender at the Leaky Cauldron the first time Harry was there?": ["Tom"]},
    {"Molly was angry at Arthur for allowing the healers to give him what Muggle medical treatment while at St. Mungo's?": ["stitches"]},
    {"Before Draco finished repairing the vanishing cabinet, he used other methods to try and kill Dumbledore, injuring two students in the process. One was Ron Weasley. Who was the other?": ["Katie", "Katie Bell"]},
    {"What was Neville's mother's first name?": ["Alice"]},
    {"What was Neville's father's first name?": ["Frank"]},
    {"Who raised Neville?": ["grandmother"]},
    {"Neville's grandmother had a hat with what type of stuffed animal on it?": ["vulture", "bird"]},
    {"What did Ginny forget on the way to King's Cross for her first year at Hogwarts?": ["diary"]},
    {"When Hagrid got back from his mission to the giants, he used a raw steak from which type of animal to help soothe his swollen eye?": ["dragon"]},
    {"The Lovegoods thought they had a Crumple-Horned Snorkack horn hanging on their wall. It was really the horn of which dangerous magical creature, which resembles a rhinocerous?": ["erumpent"]},
    {"What was the make and model of the brooms that Lucius Malfoy bought the Slytherin Quidditch team in Draco's second year?": ["Nimbus 2001"]},
    {"Who was supposed to be keeping an eye on Harry when he and Dudley were attacked by Dementors?": ["Mundungus", "Fletcher", "Mundungus Fletcher"]},
    {"Name one of the four types of Skiving Snackbox invented by Fred and George": ["Fainting Fancies", "Fever Fudge", "Nosebleed Nougat", "Puking Pastille"]},
    {"Harry, Hermione, and Draco, were three of the four students sent into the Forbidden Forest to track down the unicorn killer. Name the fourth student in the book version.": ["Neville", "Neville Longbottom"]},
    {"Harry, Hermione, and Draco, were three of the four students sent into the Forbidden Forest to track down the unicorn killer. Name the fourth student in the movie version.": ["Ron", "Ron Weasley"]},
    {"What was the name of the secret society founded by Dumbledore to oppose Voldemort and the Death Eaters?": ["Order of the Phoenix"]},
    {"Harry's friends brought a banner to his first Quidditch match that said 'Potter for President'. Which of his classmates drew a lion on the banner?": ["Dean", "Dean Thomas"]},
    {"What did Harry forget in his room when the Weasleys were breaking him out with the flying car?": ["owl", "Hedwig"]},
    {"In the book, what class did Professor McGonagall interrupt to tell Oliver Wood she had found him a new seeker?": ["charms", "Flitwick"]},
    {"In the movie, what class did Professor McGonagall interrupt to tell Oliver Wood she had found him a new seeker?": ["Defense Against the Dark Arts", "Quirrell"]},
    {"Who brought Sirius Black the list of passwords that Neville had written down?": ["Crookshanks"]},
    {"When Dumbledore visited Harry in the hospital wing at the end of the first book, he ate a single Bertie Bott's Every Flavor Bean. What flavor was he expecting it to be?": ["toffee"]},
    # {"What is the term for what happens when someone disapparates unsuccessfully, leaving part of their body behind?": ["splinch", "splinching"]},
    {"Hagrid wore a striped tie to Buckbeak's hearing. Name one of the two colors on it.": ["yellow", "orange"]},
    {"What kind of facial hair does Karkaroff have?": ["goatee"]},
    {"What color was Dumbledore's hair before he went gray?": ["auburn", "red"]},
    {"How many Galleons did the Omnioculars cost at the World Cup? ": ["10"]},
    {"On her class schedule during her second year at Hogwarts, Hermione outlined her Defense Against the Dark Arts lessons with what?": ["hearts"]},
    {"What is the term for a witch or wizard who is able to change their physical appearance at will?": ["Metamorphmagus"]},
    {"What did Mrs. Figg break in the first book that made her unable to watch Harry on Dudley's 11th birthday?": ["leg"]},
    # {"To show her support for Harry's interview in the Quibbler, Professor Sprout awarded him 20 points for passing something in class. What was the object?": ["watering can"]},
    {"Who was Ginny's date to the Yule Ball?": ["Neville", "Neville Longbottom"]},
    {"For their first Care of Magical Creatures exam, Hagrid had Harry's class keep a tub of these extremely boring creatures alive for an hour. ": ["flobberworm"]},
    {"What color is the basilisk?": ["green"]},
    {"How many Muggles did Dumbledore's father attack?": ["3"]},
    {"Which of the Marauders was referred to as having a furry little problem?": ["Moony", "Lupin", "Remus"]},
    {"What drink costs 13 sickles on the Knight Bus?": ["hot chocolate"]},
    {"While on vacation in the Isle of Wight, Aunt Marge ate something that made her sick. What was it?": ["whelk", "funny whelk"]},
    {"Which first year fell into the lake before the Start of Term Feast in Harry's fourth year?": ["Dennis Creevey", "Dennis"]},
    {"Malfoy Manor has albino animals on the grounds. What type of animal are they?": ["peacock"]},
    {"What part of Draco Malfoy was injured by Buckbeak?": ["arm"]},
    {"What did Filch claim he heard Harry was ordering when attempting to read Harry's mail?": ["Dung bombs"]},
    {"What school was Justin Fitch-Fletchley set to attend before he got his Hogwarts letter?": ["Eton"]},
    {"When Cornelius Fudge visited Azkaban, Sirius Black asked him for his newspaper, saying that he missed doing what?": ["crossword", "crossword puzzle", "crosswords"]},
    {"Dudley's school uniform included a hat made of what material?": ["straw"]},
    {"When do wizards and witches come of age?": ["17", "17th birthday"]},
    {"How many of the Hogwarts founders were women?": ["2"]},
    {"What color was the bag that the Triwizard champions pulled their dragon models out of?": ["purple"]},
    {"What material is Hagrid's hut made of?": ["wood"]},
    {"What is the name for someone who can change into an animal at will?": ["Animagus"]},
    {"When Harry lies to Professor Quirrel about what he sees in the Mirror of Erised, he says he is shaking Dumbledore's hand after winning what?": ["House Cup"]},
    {"What is the incantation for erasing memories?": ["Obliviate"]},
    {"Uncle Vernon tells everyone that Harry goes to a school for incurably criminal boys, named after which saint?": ["Saint Brutus", "Brutus"]},
    {"To which country does Hermione send her parents after erasing their memories of her?": ["Australia"]},
    {"What color was the special quill that Professor Umbridge had Harry do lines with?": ["black"]},
    {"Fred tells Ron that Hogwarts first years have to wrestle which magical creature in order to be sorted?": ["troll"]},
    {"What department does Mr. Weasley work for when Harry first meets him?": ["Misuse of Muggle Artifacts"]},
    {"Name one of the two adults, other than Uncle Vernon, that Harry asked to sign his Hogsmeade Permission slip": ["Minister", "Fudge", "McGonagall"]},
    {"Are non-humans allowed to carry wands?": ["no"]},
    {"What color robes do the members of the Wizengamot wear when they are hearing a trial?": ["plum", "purple"]},
    {"How many galleons does Dobby get paid every week when he works at Hogwarts?": ["1"]},
    {"How many days does Dobby get off each month when he works at Hogwarts?": ["1"]},
    {"Cedric Diggory's wand had a core made from which type of magical creature?": ["unicorn"]},
    {"Viktor Krum's wand had a core made from which type of magical creature?": ["dragon"]},
    {"Name one of the four Awe-roars stationed at Hogsmeade at the start of Harry's sixth year": ["Tonks", "Dawlish", "Proudfoot", "Savage"]},
    {"What is Voldemort's middle name?": ["Marvolo"]},
    {"What is engraved on the stone above Dobby's grave?": ["Here Lies Dobby A Free Elf"]},
    {"Lupin found the boggart that he used for Harry's first dementor training session in a filing cabinet in whose office?": ["Filch"]},
    # {"What color is the Age Line that Dumbledore draws around the Goblet of Fire?": ["gold"]},
    # {"At which phase of the moon must fluxweed be picked if it is to be used in Polyjuice Potion?": ["full", "full moon"]},
    {"What ingredient did Barty Crouch Junior, disguised as Moody, steal from Snape's potion stores?": ["boomslang skin"]},
    {"What breed of dog is Fang?": ["boar hound"]},
    {"Which part of his own body did Dobby iron after he made Harry and Ron miss the Hogwarts Express? ": ["hands", "fingers"]},
    {"Who did the flying motorcycle belong to?": ["Sirius", "Sirius Black"]},
    {"Name one of the four words that Dumbledore says to the school after Harry's Sorting ceremony.": ["nitwit", "blubber", "oddment", "tweak"]},
    {"Who did Harry and Ron, disguised as Crabbe and Goyle, run into by the Slytherin dungeons before Malfoy joined them?": ["Percy"]},
    {"According to the Sorting Hat, members of which house will use any means to achieve their ends?": ["Slytherin"]},
    {"According to the Sorting Hat, members of which house are just and loyal?": ["Hufflepuff"]},
    {"According to the Sorting Hat, members of which house are known for their wit and learning?": ["Ravenclaw"]},
    {"According to the Sorting Hat, members of which house are brave at heart?": ["Gryffindor"]},
    {"A Crup closely resembles which Muggle breed of dog?": ["Jack Russell", "Jack Russell terrier"]},
    {"Snape incorrectly thinks, Kappas are most commonly found,, in Mongolia. What is the correct answer?": ["Japan"]},
    {"What potion did Marcus Belby's uncle invent?": ["wolfsbane"]},
    {"Which of his fellow prefects was Percy dating in Harry's third year?": ["Penelope Clearwater", "Penelope"]},
    {"There are three known recipients of Special Awards for Services to the School: Harry, Tom Riddle, and, who else?": ["Ron", "Ron Weasley"]},
    {"What size cauldron do students use in their first year at Hogwarts?": ["2", "standard size 2"]},
    {"Who is waiting for Harry at the Leaky Cauldron at the beginning of the third book?": ["Fudge", "Cornelius Fudge", "Minister", "Hedwig"]},
    {"Where does the Knight Bus drop off Harry after he blows up Aunt Marge?": ["Leaky Cauldron", "Diagon Alley"]},
    {"What is the first name of Susan Bones's aunt, who is on the Wizengamot?": ["Amelia"]},
    {"Name the mode of travel accessed by throwing a special kind of powder on a fireplace": ["floo", "floo network"]},
    {"What is the name of an object enchanted to instantly transport anyone who touches it to a specific location?": ["portkey"]},
    {"What word did Hermione scribble at the bottom of a page she ripped out of a library book during her second year at Hogwarts?": ["pipes"]},
    {"In his fourth year at Hogwarts, Harry gave Dobby a pair of socks for Christmas. What color were they?": ["mustard", "yellow"]},
    {"What creature is in the painting in the prefect's bathroom?": ["mermaid"]},
    {"Who does Harry run into in the prefects' bathroom when he goes to listen to the egg?": ["Moaning Myrtle", "Myrtle"]},
    {"Cobbing is the name of the Quidditch foul given for excessive use of which body part?": ["elbows"]},
    {"What is the name of the witch who owns the robe shop in Diagon Alley?": ["Madam Malkin", "Malkin"]},
    {"What magical creature has the body, hind legs, and tail of a horse but the front legs, wings, and head of a giant eagle?": ["hippogriff"]},
    {"What color is a Bludger?": ["black"]},
    {"What color is a Quaffle?": ["red"]},
    {"What color is a Snitch?": ["gold"]},
    {"What is Tonks and Lupin's son's name?": ["Teddy"]},
    {"Who is Teddy's godfather?": ["Harry", "Harry Potter"]},
    {"How many presents did Dudley Dursley ultimately receive for his 11th birthday?": ["38"]},
    {"In the books, is it ever confirmed that Draco received the Dark Mark?": ["no"]},
    {"On what item of Harry's does Hermione cast an Impervius Charm?": ["glasses", "goggles"]},
    {"While at Hogwarts, Cho Chang dated three boys: Cedric Diggory, Harry Potter, and who else?": ["Michael Corner", "Michael"]},
    {"What part of the Monster Book of Monsters do you stroke to open it?": ["spine", "side"]},
    {"What is Harry's scar shaped like?": ["lightning", "bolt"]},
    {"Who was Colin Creevey on his way to visit in the hospital wing when he was petrified?": ["Harry", "Harry Potter"]},
    {"Which prefect was petrified by the basilisk?": ["Penelope Clearwater", "Penelope"]},
    {"Who was the Hufflepuff student petrified by the basilisk?": ["Justin Finch-Fletchley"]},
    {"Which house did not have any students petrified by the basilisk?": ["Slytherin"]},
    {"Who gave Harry a book on how to charm witches for his 17th birthday?": ["Ron", "Ron Weasley"]},
    {"When Harry and Ron showed up for their first breakfast at Hogwarts during their second year, Hermione was reading a book written by which author?": ["Lockhart", "Gilderoy Lockhart"]},
    {"For the Defense Against the Dark Arts final at the end of his third year, Harry had to complete an obstacle course with a boggart, grin-dee-lows, hink-ee-punks, and which other creature, which are goblin-like and lurk wherever there has been bloodshed?": ["Red Caps"]},
    {"What by-product is collected from bubotubers?": ["pus"]},
    # {"What is the only antidote to basilisk venom?": ["phoenix tears"]},
    {"Which student did Moaning Myrtle haunt after her death?": ["Olive Hornby"]},
    {"According to Dumbledore's chocolate frog card, what type of music does he enjoy?": ["chamber", "chamber music"]},
    {"According to Dumbledore's chocolate frog card, what activity does he enjoy?": ["ten pin bowling", "bowling"]},
    {"What flavor lollipops can be found in the unusual tastes section of Honeydukes?": ["blood"]},
    {"What form does Arthur Weasley's Patronus take?": ["weasel"]},
    {"What did Mr. Weasley add to Molly's tea the morning he returned from the Quidditch World Cup?": ["firewhiskey", "whiskey", "alcohol", "booze", "liquor"]},
    {"Where did Hagrid meet the man who gave him Norbert's egg?": ["Hogs Head", "pub", "bar"]},
    {"What was the name of the dog that Aunt Marge brought with her when she visited her brother?": ["Ripper"]},
    {"On Harry's first night at Hogwarts, he had a dream where he was told he should transfer to another house at once, because it was his destiny. Which house?": ["Slytherin"]},
    {"There were two possible side effects listed for the Patented Daydream Charms Harry saw at Weasley's Wizarding Wheezes: vacant expression and minor what?": ["drooling", "drool"]},
    {"What was the original term used to identify the Deluminator?": ["Put Outer"]},
    {"How did Hagrid get to the Ministry for Buckbeak's hearing?": ["Knight Bus"]},
    {"When the school had to spend the night in the great hall after Sirius Black attacked the Fat Lady, what color sleeping bags were the students provided with?": ["purple"]},
    {"What body part is Mad-Eye Moody missing, other than his eye?": ["leg"]},
    {"What did Sirius give Harry for his first birthday?": ["broom", "broomstick", "toy broom", "toy broomstick"]},
    {"What famous wizard was on Harry's first Chocolate Frog card?": ["Dumbledore"]},
    {"What curse did Barty Crouch Senior predominantly use to keep his son under house arrest?": ["ImperiusImperius Curse", "Imperio"]},
    {"What color handbag does Neville's grandma carry?": ["red"]},
    {"Who did Ron inherit his wand from?": ["Charlie"]},
    {"Who did ron inherit Scabbers from?": ["Percy"]},
    {"What did Hagrid pack in Norbert's crate, in case he got lonely?": ["teddy", "teddy bear"]},
    {"Who gave Pigwidgeon to Ron?": ["Sirius", "Sirius Black"]},
    {"Who named Pigwidgeon?": ["Ginny"]},
    {"What is the name of Ron's tiny pet owl?": ["Pig", "Pigwidgeon"]},
    {"How old was Harry turning when he received his first-ever birthday card?": ["13"]},
    {"What do wizards call people with no magical blood?": ["Muggle"]},
    # {"What is a wizarding slur for Muggle-born wizards?": ["Mudblood"]},
    {"In his first year, Harry saw Snape in the staffroom with a bloodied leg. Who was bandaging it for him?": ["Filch", "Argus Filch"]},
    {"Name the popular candy that is sold packaged with collectible cards": ["chocolate frog"]},
    # {"How many years did Sirius spend in Azkaban? ": ["12"]},
    {"What is the incantation that makes you dance uncontrollably?": ["Tarantallegra"]},
    {"How many points for throwing something through Myrtle's head?": ["50"]},
    {"What was Dean's favorite football team?": ["West Ham"]},
    {"Ludo Bagman wore his old Quidditch robes to the World Cup. What two colors were they?": ["black and yellow", "yellow and black", "black and gold", "gold and black"]},
    {"What Quidditch position did Ludo Bagman play?": ["Beater"]},
    {"Which piece did Ron play as during the chess match at the end of the first book?": ["Knight"]},
    {"Which piece did Harry play as during the chess match at the end of the first book?": ["Bishop"]},
    {"Name one food that Harry cooked for breakfast on Dudley's 11th birthday.": ["bacon", "eggs"]},
    {"How many breeds of dragon are native to Britain?": ["2"]},
    {"What is the name of the most popular wizard-ing newspaper in Britain?": ["Daily Prophet"]},
    {"24 copies of Harry's Hogwarts letter, found their way into Privet Drive, hidden inside which grocery item?": ["eggs"]},
    {"Which class does Firenze teach?": ["Divination"]},
    {"The Whomping Willow was planted because of which Hogwarts student?": ["Lupin", "Remus", "Remus Lupin"]},
    {"Which subject did Charity Burbage teach at Hogwarts?": ["Muggle Studies"]},
    {"Name one of the three Muggle things that Harry explained to Mr. Weasley during his first visit to the Burrow?": ["postal service", "post", "mail", "plugs", "phones", "telephones", "post office"]},
    {"What is Neville's toad's name?": ["Trevor"]},
    {"Who used a levitating charm to put Nifflers in Umbridge's office?": ["Lee", "Lee Jordan"]},
    {"What color is Ginny's pet pygmy puff?": ["purple"]},
    {"Who was with Harry, Ron, and Hermione when they first met Fluffy?": ["Neville", "Neville Longbottom"]},
    {"Who taught Care of Magical Creatures while Hagrid was visiting the giants?": ["Professor Grubbly Plank", "Grubbly Plank"]},
    {"What color are unicorn foals?": ["gold"]},
    {"What color are basilisks?": ["green"]},
    {"How many broomsticks did Sirius buy Harry?": ["2"]},
    {"How many galleons did Harry get for winning the Triwizard Tournament?": ["1000"]},
    {"Who did Ron assume let the troll in, on Halloween?": ["Peeves"]},
    {"As their final prank before leaving Hogwarts, the Weasley twins turned the fifth floor corridor into what?": ["swamp", "marsh"]},
    {"What did Fred and George want to send Harry when he was in the hospital wing his first year at Hogwarts?": ["toilet seat"]},
    {"Four students impersonated Dementors during a Quidditch game in Harry's third year: Malfoy, Crabbe, Goyle, and who else?": ["Marcus Flint", "Flint", "Marcus"]},
    {"Who gave Harry an eagle-feather quill for Christmas his second year at Hogwarts?": ["Hermione"]},
    {"For how many months was Draco unable to use his arm after being attacked by Buckbeak?": ["3"]},
    {"What creature, also known as a water demon, has long fingers that are strong but brittle and easily broken?": ["grindylow"]},
    {"What is the name of the village that the Weasleys, Diggorys, and Lovegoods live near?": ["Ottery St. Catchpole"]},
    {"What did George lose during the escape from Privet Drive?": ["ear"]},
    {"What did students wear in Herbology to protect themselves from the mandrakes?": ["ear muffs"]},
    {"What color is the telephone box used as the visitor's entrance to the Ministry of Magic?": ["red"]},
    {"The first spell Harry cast when he turned 17 was Accio. What was he summoning?": ["glasses"]},
    {"In Harry's fourth year, Snape threatened to spike which of his drinks with truth potion?": ["pumpkin juice"]},
    {"What color was Quirrel's turban?": ["purple"]},
    {"In which body of water is Azkaban located?": ["North Sea"]},
    {"Who sits in on Harry's career advising appointment with McGonagall?": ["Umbridge"]},
    # {"One Neville is worth how many Malfoys, according to Neville during a Quidditch match their first year?": ["12"]},
    {"What color was Tom Riddle's diary?": ["black"]},
    {"What is Aberforth Dumbledore's Patronus?": ["goat"]},
    {"What is Albus Dumbledore's Patronus?": ["phoenix"]},
    {"What is Ginny's Patronus?": ["horse"]},
    {"What is Harry's Patronus?": ["stag"]},
    {"What is Luna's Patronus?": ["hare"]},
    {"What is McGonagall's Patronus?": ["cat", "3 cats"]},
    {"Tonks's Patronus starts out as a rabbit, but then changes to which animal?": ["wolf"]},
    {"What is Umbridge's Patronus?": ["cat"]},
    {"Are flying carpets legal?": ["no"]},
    {"What kind of sandwich did Molly pack for Ron on his first trip to Hogwarts?": ["corned beef", "beef"]},
    {"What color is the Knight Bus?": ["purple"]},
    {"Who brought Harry to Kings Cross for his first year at Hogwarts?": ["Dursleys", "Vernon"]},
    {"Dumbledore told Harry, that he saw himself holding, what, when he looked into the Mirror of Erised?": ["socks", "wool socks"]},
    {"What is the charm used to make a person confused?": ["Confundus Charm", "Confundo", "Confundus"]}
    ]