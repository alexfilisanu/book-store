import os

import psycopg2
import jwt
from flask import Flask, request, jsonify
from flask_cors import CORS
from functools import wraps
from flasgger import Swagger

app = Flask(__name__)
CORS(app)
swagger = Swagger(app)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "my-secret-key")


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(current_user_id, *args, **kwargs)

    return decorated


@app.route('/total-books', methods=['GET'])
@token_required
def get_total_books(user_id):
    """
    Get the total number of books in the database.
    ---
    responses:
      200:
        description: Total number of books
        schema:
          type: object
          properties:
            totalBooks:
              type: integer
              example: 100
      500:
        description: Internal server error
    """
    search_query = request.args.get('q', '')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT 
            COUNT(*) 
        FROM 
            books b
        WHERE
            b.Book_Title ILIKE %s
            OR b.Book_Author ILIKE %s
            OR b.ISBN ILIKE %s;
        """
        cursor.execute(query, (
            f"%{search_query}%",
            f"%{search_query}%",
            f"{search_query}"
        ))
        total_books = cursor.fetchone()[0]

        conn.close()
        return jsonify({"totalBooks": total_books}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/books', methods=['GET'])
@token_required
def get_books(user_id):
    """
    Get a list of books based on search query.
    ---
    parameters:
      - name: q
        in: query
        required: false
        description: Search query for book title, author, or ISBN
        schema:
          type: string
      - name: page
        in: query
        required: false
        description: Page number for pagination
        schema:
          type: string
      - name: limit
        in: query
        required: false
        description: Number of books per page
        schema:
          type: integer
    responses:
      200:
        description: List of books
        schema:
          type: object
          properties:
            books:
              type: array
              items:
                type: object
                properties:
                  ISBN:
                    type: string
                  Book_Title:
                    type: string
                  Book_Author:
                    type: string
                  Image_URL:
                    type: string
                  Average_Rating:
                    type: number
                  Price:
                    type: number
      500:
        description: Internal server error
    """
    search_query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    offset = (page - 1) * limit

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT 
            b.ISBN,
            b.Book_Title,
            b.Book_Author,
            b.Image_URL,
            COALESCE(AVG(r.Book_Rating), 0) AS Average_Rating,
            i.Price
        FROM 
            books b
        LEFT JOIN 
            ratings r ON b.ISBN = r.ISBN
        LEFT JOIN 
            inventory i ON b.ISBN = i.ISBN
        WHERE
            b.Book_Title ILIKE %s
            OR b.Book_Author ILIKE %s
            OR b.ISBN ILIKE %s
        GROUP BY 
            b.ISBN, i.Price
        ORDER BY 
            Average_Rating DESC
        LIMIT %s OFFSET %s;
        """
        cursor.execute(query, (
            f"%{search_query}%",
            f"%{search_query}%",
            f"{search_query}",
            limit,
            offset
        ))
        books = cursor.fetchall()

        books_list = [
            {
                "ISBN": row[0],
                "Book_Title": row[1],
                "Book_Author": row[2],
                "Image_URL": row[3],
                "Average_Rating": round(row[4], 2),
                "Price": float(row[5]) if row[5] is not None else 0.0
            }
            for row in books
        ]

        conn.close()
        return jsonify({"books": books_list}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/book', methods=['GET'])
@token_required
def get_book(user_id):
    """
    Get book details by ISBN.
    ---
    parameters:
      - name: isbn
        in: query
        required: true
        description: ISBN of the book
        schema:
          type: string
    responses:
      200:
        description: Book details
        schema:
          type: object
          properties:
            book:
              type: object
              properties:
                ISBN:
                  type: string
                Book_Title:
                  type: string
                Book_Author:
                  type: string
                Year_Of_Publication:
                  type: integer
                Publisher:
                  type: string
                Image_URL:
                  type: string
                Average_Rating:
                  type: number
                Quantity:
                  type: integer
                Price:
                  type: number
      404:
        description: Book not found
      500:
        description: Internal server error
    """
    isbn = request.args.get('isbn', '')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT
            b.ISBN, 
            b.Book_Title,
            b.Book_Author,
            b.Year_Of_Publication,
            b.Publisher,
            b.Image_URL,
            COALESCE(AVG(r.Book_Rating), 0) AS Average_Rating,
            i.Quantity,
            i.Price
        FROM 
            books b
        LEFT JOIN 
            ratings r ON b.ISBN = r.ISBN
        LEFT JOIN 
            inventory i ON b.ISBN = i.ISBN
        WHERE
            b.ISBN = %s
        GROUP BY 
            b.ISBN, i.Quantity, i.Price;
        """
        cursor.execute(query, (isbn,))
        book = cursor.fetchone()

        if book is None:
            return jsonify({"error": "Book not found"}), 404

        book_dict = {
            "ISBN": book[0],
            "Book_Title": book[1],
            "Book_Author": book[2],
            "Year_Of_Publication": book[3],
            "Publisher": book[4],
            "Image_URL": book[5],
            "Average_Rating": round(book[6], 2),
            "Quantity": book[7] if book[7] is not None else 0,
            "Price": float(book[8]) if book[8] is not None else 0.0
        }

        conn.close()
        return jsonify({"book": book_dict}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/total-reviews', methods=['GET'])
@token_required
def get_my_total_reviews(user_id):
    """
    Get the total number of reviews for the logged-in user.
    ---
    responses:
      200:
        description: Total number of reviews
        schema:
          type: object
          properties:
            totalReviews:
              type: integer
              example: 50
      500:
        description: Internal server error
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT
            COUNT(*)
        FROM
            ratings
        WHERE
            User_ID = %s;
        """
        cursor.execute(query, (user_id,))
        total_reviews = cursor.fetchone()[0]

        conn.close()
        return jsonify({'totalReviews': total_reviews}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/reviews', methods=['GET'])
@token_required
def get_my_reviews(user_id):
    """
    Get reviews for the logged-in user.
    ---
    parameters:
      - name: page
        in: query
        required: false
        description: Page number for pagination
        schema:
          type: integer
      - name: limit
        in: query
        required: false
        description: Number of reviews per page
        schema:
          type: integer
    responses:
      200:
        description: List of reviews
        schema:
          type: object
          properties:
            reviews:
              type: array
              items:
                type: object
                properties:
                  ISBN:
                    type: string
                  Book_Title:
                    type: string
                  Book_Author:
                    type: string
                  Image_URL:
                    type: string
                  Average_Rating:
                    type: number
                  Price:
                    type: number
      500:
        description: Internal server error
    """
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    offset = (page - 1) * limit

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT
            b.ISBN,
            b.Book_Title,
            b.Book_Author,
            b.Image_URL,
            r.Book_Rating,
            i.Price
        FROM
            ratings r
        JOIN
            books b ON r.ISBN = b.ISBN
        LEFT JOIN
            inventory i ON b.ISBN = i.ISBN
        WHERE
            r.User_ID = %s
        ORDER BY
            r.Book_Rating DESC
        LIMIT %s OFFSET %s;
        """
        cursor.execute(query, (user_id, limit, offset))
        reviews = cursor.fetchall()

        reviews_list = [
            {
                "ISBN": row[0],
                "Book_Title": row[1],
                "Book_Author": row[2],
                "Image_URL": row[3],
                "Average_Rating": row[4],
                "Price": float(row[5]) if row[5] is not None else 0.0
            }
            for row in reviews
        ]

        conn.close()
        return jsonify({'reviews': reviews_list}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/book/review/status', methods=['GET'])
@token_required
def get_review_status(user_id):
    """
    Get the review status for a book.
    ---
    parameters:
      - name: isbn
        in: query
        required: true
        description: ISBN of the book
        schema:
          type: string
    responses:
      200:
        description: Review status
        schema:
          type: object
          properties:
            bookRating:
              type: integer
      400:
        description: Bad request
      500:
        description: Internal server error
    """
    isbn = request.args.get('isbn')

    if not isbn:
        return jsonify({'error': 'Missing required data'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT
            Book_Rating
        FROM
            ratings
        WHERE
            User_ID = %s
            AND ISBN = %s;
        """
        cursor.execute(query, (user_id, isbn))
        book_rating = cursor.fetchone()

        conn.close()
        return jsonify({'bookRating': book_rating}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/book/review', methods=['POST'])
@token_required
def add_book_review(user_id):
    """
    Add a review for a book.
    ---
    parameters:
      - name: isbn
        in: body
        required: true
        description: ISBN of the book
        schema:
          type: string
      - name: rating
        in: body
        required: true
        description: Rating for the book
        schema:
          type: integer
    responses:
      200:
        description: Review added successfully
      400:
        description: Bad request
      500:
        description: Internal server error
    """
    data = request.json
    if not data:
        return jsonify({'No data provided'}), 400

    isbn = data.get('isbn')
    rating = int(data.get('rating'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        INSERT INTO 
            ratings (User_ID, ISBN, Book_Rating)
        VALUES 
            (%s, %s, %s);
        """
        cursor.execute(query, (user_id, isbn, rating))
        conn.commit()

        conn.close()
        return jsonify({"message": "Review added successfully"}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/cart', methods=['POST'])
@token_required
def add_to_cart(user_id):
    """
    Add a book to the cart.
    ---
    parameters:
      - name: isbn
        in: body
        required: true
        description: ISBN of the book
        schema:
          type: string
    responses:
      200:
        description: Book added to cart
      400:
        description: Bad request
      500:
        description: Internal server error
    """
    data = request.json
    if not data:
        return jsonify({'No data provided'}), 400

    isbn = data.get('isbn')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        insert_query = """
        INSERT INTO cart_items (User_ID, ISBN)
        VALUES (%s, %s);
        """
        cursor.execute(insert_query, (user_id, isbn))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Book added to cart'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/cart', methods=['DELETE'])
@token_required
def remove_from_cart(user_id):
    """
    Remove a book from the cart.
    ---
    parameters:
      - name: isbn
        in: body
        required: true
        description: ISBN of the book
        schema:
          type: string
    responses:
      200:
        description: Book removed from cart
      400:
        description: Bad request
      500:
        description: Internal server error
    """
    data = request.json
    if not data:
        return jsonify({'No data provided'}), 400

    isbn = data.get('isbn')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        delete_query = """
        DELETE FROM cart_items
        WHERE User_ID = %s AND ISBN = %s;
        """
        cursor.execute(delete_query, (user_id, isbn))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Book removed from cart'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/total-cart', methods=['GET'])
@token_required
def get_total_cart(user_id):
    """
    Get the total number of books in the cart.
    ---
    responses:
      200:
        description: Total number of books in the cart
        schema:
          type: object
          properties:
            totalBooksCart:
              type: integer
              example: 5
      500:
        description: Internal server error
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT
            COUNT(*)
        FROM
            cart_items
        WHERE
            User_ID = %s;
        """
        cursor.execute(query, (user_id,))
        total_books = cursor.fetchone()[0]

        conn.close()
        return jsonify({'totalBooksCart': total_books}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/cart', methods=['GET'])
@token_required
def get_books_cart(user_id):
    """
    Get books in the cart.
    ---
    parameters:
      - name: page
        in: query
        required: false
        description: Page number for pagination
        schema:
          type: string
      - name: limit
        in: query
        required: false
        description: Number of books per page
        schema:
          type: integer
    responses:
      200:
          description: List of books in the cart
          schema:
            type: object
            properties:
              booksCart:
                type: array
                items:
                  type: object
                  properties:
                    ISBN:
                      type: string
                    Book_Title:
                      type: string
                    Book_Author:
                      type: string
                    Image_URL:
                      type: string
                    Average_Rating:
                      type: number
                    Price:
                      type: number
      500:
        description: Internal server error
    """
    page = request.args.get('page')
    limit = request.args.get('limit')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT
            b.ISBN,
            b.Book_Title,
            b.Book_Author,
            b.Image_URL,
            COALESCE(AVG(r.Book_Rating), 0) AS Average_Rating,
            i.Price
        FROM
            cart_items c
        JOIN
            books b ON c.ISBN = b.ISBN
        LEFT JOIN
            ratings r ON b.ISBN = r.ISBN
        LEFT JOIN
            inventory i ON b.ISBN = i.ISBN
        WHERE
            c.User_ID = %s
        GROUP BY 
            b.ISBN, b.Book_Title, b.Book_Author, b.Image_URL, i.Price
        """

        params = [user_id]
        if page and limit:
            offset = (int(page) - 1) * int(limit)
            query += " LIMIT %s OFFSET %s"
            params += [int(limit), offset]

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        books = [{
            "ISBN": row[0],
            "Book_Title": row[1],
            "Book_Author": row[2],
            "Image_URL": row[3],
            "Average_Rating": round(row[4], 2),
            "Price": float(row[5]) if row[5] is not None else 0.0
        } for row in rows]

        conn.close()
        return jsonify({'booksCart': books}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/order', methods=['POST'])
@token_required
def place_order(user_id):
    """
    Place an order for the books in the cart.
    ---
    parameters:
      - name: address
        in: body
        required: true
        description: Shipping address for the order
        schema:
          type: string
      - name: items
        in: body
        required: true
        description: List of books in the cart
        schema:
          type: array
          items:
            type: object
            properties:
              isbn:
                type: string
    responses:
      200:
        description: Order placed successfully
      400:
        description: Bad request
      500:
        description: Internal server error
    """
    data = request.get_json()

    address = data.get('address')
    items = data.get('items', [])

    if not user_id or not address or not items:
        return jsonify({'error': 'Missing required data'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        for item in items:
            isbn = item['isbn']
            cursor.execute("""
                SELECT Quantity FROM inventory WHERE ISBN = %s;
            """, (isbn,))
            result = cursor.fetchone()

            if not result:
                return jsonify({'error': f'Cartea cu ISBN {isbn} nu există în stoc.'}), 400

        cursor.execute("""
            INSERT INTO orders (User_ID, Address)
            VALUES (%s, %s)
            RETURNING Order_ID;
        """, (user_id, address))
        order_id = cursor.fetchone()[0]

        for item in items:
            isbn = item['isbn']
            cursor.execute("""
                INSERT INTO order_items (Order_ID, ISBN)
                VALUES (%s, %s);
            """, (order_id, isbn))

            cursor.execute("""
                UPDATE inventory
                SET Quantity = Quantity - %s
                WHERE ISBN = %s;
            """, (1, isbn))

            cursor.execute("""
                DELETE FROM cart_items
                WHERE User_ID = %s AND ISBN = %s;
            """, (user_id, isbn))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Order placed successfully!'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/cart/check', methods=['GET'])
@token_required
def check_if_in_cart(user_id):
    """
    Check if a book is in the cart.
    ---
    parameters:
      - name: isbn
        in: query
        required: true
        description: ISBN of the book
        schema:
          type: string
    responses:
      200:
        description: Book in cart status
        schema:
          type: object
          properties:
            inCart:
              type: boolean
              example: true
      400:
        description: Bad request
      500:
        description: Internal server error
    """
    isbn = request.args.get('isbn')

    if not isbn:
        return jsonify({'error': 'Missing required data'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1 FROM cart_items WHERE User_ID = %s AND ISBN = %s
    """, (user_id, isbn))
    result = cursor.fetchone()
    conn.close()

    return jsonify({'inCart': bool(result)})


@app.route('/admin/book', methods=['PUT'])
@token_required
def update_book(user_id):
    """
    Update book details.
    ---
    parameters:
      - name: isbn
        in: body
        required: true
        description: ISBN of the book
        schema:
          type: string
      - name: price
        in: body
        required: false
        description: New price for the book
        schema:
          type: number
      - name: quantity
        in: body
        required: false
        description: New quantity for the book
        schema:
          type: integer
    responses:
      200:
        description: Book updated successfully
      400:
        description: Bad request
      500:
        description: Internal server error
    """
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    isbn = data.get('isbn')
    price = data.get('price')
    quantity = data.get('quantity')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if price is not None:
            cursor.execute("""
                UPDATE inventory
                SET Price = %s
                WHERE ISBN = %s;
            """, (price, isbn))

        if quantity is not None:
            cursor.execute("""
                UPDATE inventory
                SET Quantity = %s
                WHERE ISBN = %s;
            """, (quantity, isbn))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Book updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/book', methods=['DELETE'])
@token_required
def delete_book(user_id):
    """
    Delete a book from the database.
    ---
    parameters:
      - name: isbn
        in: query
        required: true
        description: ISBN of the book
        schema:
          type: string
    responses:
      200:
        description: Book deleted successfully
      400:
        description: Bad request
      500:
        description: Internal server error
    """
    isbn = request.args.get('isbn')

    if not isbn:
        return jsonify({'error': 'Missing required data'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM books
            WHERE ISBN = %s;
        """, (isbn,))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Book deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/book', methods=['POST'])
@token_required
def add_book(user_id):
    """
    Add a new book to the database.
    ---
    parameters:
      - name: isbn
        in: body
        required: true
        description: ISBN of the book
        schema:
          type: string
      - name: title
        in: body
        required: true
        description: Title of the book
        schema:
          type: string
      - name: author
        in: body
        required: true
        description: Author of the book
        schema:
          type: string
      - name: year
        in: body
        required: true
        description: Year of publication
        schema:
          type: integer
      - name: publisher
        in: body
        required: true
        description: Publisher of the book
        schema:
          type: string
      - name: image
        in: body
        required: true
        description: Image URL of the book
        schema:
          type: string
      - name: price
        in: body
        required: true
        description: Price of the book
        schema:
          type: number
      - name: quantity
        in: body
        required: true
        description: Quantity of the book
        schema:
          type: integer
    responses:
      200:
        description: Book added successfully
      400:
        description: Bad request
      500:
        description: Internal server error
    """
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    isbn = data.get('isbn')
    title = data.get('title')
    author = data.get('author')
    year = data.get('year')
    publisher = data.get('publisher')
    image = data.get('image')
    price = data.get('price')
    quantity = data.get('quantity')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO books (ISBN, Book_Title, Book_Author, Year_Of_Publication, Publisher, Image_URL)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (isbn, title, author, year, publisher, image))

        cursor.execute("""
            INSERT INTO inventory (ISBN, Price, Quantity)
            VALUES (%s, %s, %s);
        """, (isbn, price, quantity))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Book added successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/stats/orders-per-month', methods=['GET'])
@token_required
def orders_per_month(user_id):
    """
    Get the number of orders placed per month.
    ---
    parameters:
      - name: year
        in: query
        required: false
        description: Year to filter orders
        schema:
          type: integer
    responses:
      200:
        description: List of orders per month
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: object
                properties:
                  month:
                    type: string
                  orderCount:
                    type: integer
      500:
        description: Internal server error
      400:
        description: Bad request
    """
    year = request.args.get('year')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if year:
            cursor.execute("""
                SELECT DATE_TRUNC('month', Order_Date) as Month, COUNT(*) as OrderCount
                FROM orders
                WHERE EXTRACT(YEAR FROM Order_Date) = %s
                GROUP BY Month
                ORDER BY Month;
            """, (year,))
        else:
            cursor.execute("""
                SELECT DATE_TRUNC('month', Order_Date) as Month, COUNT(*) as OrderCount
                FROM orders
                GROUP BY Month
                ORDER BY Month;
            """)

        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                'month': row[0].strftime('%Y-%m'),
                'orderCount': row[1]
            })

        conn.close()
        return jsonify({'data': result}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/stats/publisher-distribution', methods=['GET'])
@token_required
def publisher_distribution(user_id):
    """
    Get the distribution of books by publisher.
    ---
    responses:
      200:
        description: List of publishers with book counts
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: object
                properties:
                  publisher:
                    type: string
                  booksCount:
                    type: integer
      500:
        description: Internal server error
      400:
        description: Bad request
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT Publisher, COUNT(*) as BooksCount
            FROM books
            GROUP BY Publisher
            ORDER BY BooksCount DESC;
        """)

        rows = cursor.fetchall()

        top_publishers = []
        others_count = 0

        for idx, row in enumerate(rows):
            publisher = row[0] if row[0] else 'Unknown'
            books_count = row[1]

            if idx < 10:
                top_publishers.append({
                    'publisher': publisher,
                    'booksCount': books_count
                })
            else:
                others_count += books_count

        if others_count > 0:
            top_publishers.append({
                'publisher': 'Others',
                'booksCount': others_count
            })

        conn.close()
        return jsonify({'data': top_publishers}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/stats/earnings-per-month', methods=['GET'])
@token_required
def earnings_per_month(user_id):
    """
    Get the total earnings per month.
    ---
    parameters:
      - name: year
        in: query
        required: true
        description: Year to filter earnings
        schema:
          type: integer
    responses:
      200:
        description: List of earnings per month
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: object
                properties:
                  month:
                    type: string
                  earnings:
                    type: number
      500:
        description: Internal server error
      400:
        description: Bad request
    """
    try:
        year = request.args.get('year', type=int)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                TO_CHAR(o.Order_Date, 'YYYY-MM') AS month,
                SUM(i.Price) AS total_earnings
            FROM
                orders o
            JOIN
                order_items oi ON o.Order_ID = oi.Order_ID
            JOIN
                inventory i ON oi.ISBN = i.ISBN
            WHERE
                EXTRACT(YEAR FROM o.Order_Date) = %s
            GROUP BY
                month
            ORDER BY
                month;
        """, (year,))

        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                'month': row[0],
                'earnings': float(row[1]) if row[1] else 0.0
            })

        conn.close()
        return jsonify({'data': result}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=3050, host='0.0.0.0')
