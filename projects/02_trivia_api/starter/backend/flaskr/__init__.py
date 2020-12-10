import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin
import random
import json
from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
    Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    '''
    CORS(app)
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
    '''
    Use the after_request decorator to set Access-Control-Allow
    '''

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
        return response

    @app.route("/api/categories", methods=['GET'])
    @cross_origin()
    def get_categories():
        categories = Category.query.all()
        if len(categories) == 0:
            abort(404)
        return jsonify({'categories': [category.format() for category in categories]})

    '''
    Create an endpoint to handle GET requests for questions, 
    including pagination (every 10 questions). 
    This endpoint should return a list of questions, 
    number of total questions, current category, categories. 
    
    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions. 
    '''

    @app.route("/api/questions", methods=['GET'])
    @cross_origin()
    def get_questions():
        questions = Question.query.paginate(per_page=QUESTIONS_PER_PAGE)
        categories = Category.query.all()

        if len(questions.items) == 0:
            abort(404)
        return jsonify({
            'questions': list(map(lambda question: question.format(), questions.items)),
            'categories': [category.format() for category in categories],
            'total_questions': questions.total
        })

    '''
    Create an endpoint to DELETE question using a question ID. 
  
    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page. 
    '''

    @app.route("/api/questions/<int:question_id>", methods=['DELETE'])
    @cross_origin()
    def delete_question(question_id):
        question = Question.query.filter_by(id=question_id).first()
        try:
            question.delete()
            return jsonify({'success': True})
        except:
            abort(500)

    '''
    Create an endpoint to POST a new question, 
    which will require the question and answer text, 
    category, and difficulty score.
  
    TEST: When you submit a question on the "Add" tab, 
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.  
    '''

    @app.route("/api/questions", methods=['POST'])
    @cross_origin()
    def create_a_question():
        data_json = request.data
        args = json.loads(data_json)
        question = Question(
            args['question'],
            args['answer'],
            args['category'],
            args['difficulty']
        )
        try:
            question.insert()
            return jsonify({'success': True})
        except:
            abort(500)

    '''
    Create a POST endpoint to get questions based on a search term. 
    It should return any questions for whom the search term 
    is a substring of the question. 
  
    TEST: Search by any phrase. The questions list will update to include 
    only question that include that string within their question. 
    Try using the word "title" to start. 
    '''

    @app.route("/api/questions/list", methods=['POST'])
    @cross_origin()
    def search_venues():
        data_json = request.data
        args = json.loads(data_json)
        questions_query = Question.query.filter(Question.question.ilike('%' + args['searchTerm'] + '%'))
        question_list = list(map(Question.format, questions_query))
        return jsonify({
            'questions': question_list,
            'total_questions': len(question_list),
            'current_category': {}
        })

    '''
    Create a GET endpoint to get questions based on category. 
  
    TEST: In the "List" tab / main screen, clicking on one of the 
    categories in the left column will cause only questions of that 
    category to be shown. 
    '''

    @app.route("/api/categories/<int:category_id>/questions", methods=['GET'])
    @cross_origin()
    def get_questions_of_a_category(category_id):
        questions = Question.query.filter_by(category=category_id).paginate(per_page=QUESTIONS_PER_PAGE)
        categories = Category.query.all()

        if len(questions.items) == 0:
            abort(404)
        return jsonify({
            'questions': list(map(lambda question: question.format(), questions.items)),
            'categories': [category.format() for category in categories],
            'total_questions': questions.total,
            'current_category': list(filter(lambda category: category.id == category_id, categories)).pop().format()
        })

    '''
    Create a POST endpoint to get questions to play the quiz. 
    This endpoint should take category and previous question parameters 
    and return a random questions within the given category, 
    if provided, and that is not one of the previous questions. 
  
    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not. 
    '''

    @app.route("/api/quizzes", methods=['POST'])
    @cross_origin()
    def get_quiz_question():
        data_json = request.data
        args = json.loads(data_json)
        category_id = args['quiz_category']['id']
        previous_questions = args['previous_questions']

        try:
            '''
            Gets list of questions of each category
            '''
            questions = Question.query.filter_by(category=category_id)
            '''
            Gets count of all questions
            '''
            if questions.count() > len(previous_questions):
                '''
                Gets new questions if there is already some questions
                '''
                if len(previous_questions) > 0:
                    questions = questions.filter(Question.id.notin_(previous_questions))
                print(len(previous_questions))
                '''
                Retrieves the questions
                '''
                records = list(map(Question.format, questions.all()))
                '''
                Extracts all ids
                '''
                ids = list(map(lambda q: q['id'], records))
                '''
                Gets the random id
                '''
                random_id = random.randint(0, len(ids) - 1)
                new_question = records[random_id]
            else:
                '''
                No more questions just return None to finalize the result
                '''
                new_question = None

            return jsonify({
                'question': new_question
            })
        except:
            abort(500)

    '''
    Create error handlers for all expected errors 
    including 404 and 422. 
    '''

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Not found"
        }), 404

    @app.errorhandler(422)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "The request cannot be processed"
        }), 422

    @app.errorhandler(500)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Internal server"
        }), 500

    return app
