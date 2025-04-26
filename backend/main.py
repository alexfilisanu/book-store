import os

import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


@app.route('/total-books', methods=['GET'])
def get_total_books():
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
def get_books():
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


@app.route('/book/<isbn>/', methods=['GET'])
def get_book(isbn):
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
def get_my_total_reviews():
    user_id = int(request.args.get('userId'))

    if not user_id:
        return jsonify({'error': 'Missing required data'}), 400

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
def get_my_reviews():
    user_id = request.args.get('userId')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    offset = (page - 1) * limit

    if not user_id:
        return jsonify({'error': 'Missing required data'}), 400

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
def get_review_status():
    user_id = int(request.args.get('userId'))
    isbn = request.args.get('isbn')

    if not user_id or not isbn:
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
def add_book_review():
    data = request.json
    if not data:
        return jsonify({'No data provided'}), 400

    user_id = int(data.get('userId'))
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
def add_to_cart():
    data = request.json
    if not data:
        return jsonify({'No data provided'}), 400

    user_id = int(data.get('userId'))
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


@app.route('/total-cart', methods=['GET'])
def get_total_cart():
    user_id = request.args.get('userId')

    if not user_id:
        return jsonify({'error': 'Missing required data'}), 400

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
def get_books_cart():
    user_id = request.args.get('userId')
    page = request.args.get('page')
    limit = request.args.get('limit')

    if not user_id:
        return jsonify({'error': 'Missing required data'}), 400

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
def place_order():
    data = request.get_json()

    user_id = data.get('userId')
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
def check_if_in_cart():
    user_id = request.args.get('userId')
    isbn = request.args.get('isbn')

    if not user_id or not isbn:
        return jsonify({'error': 'Missing required data'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1 FROM cart_items WHERE User_ID = %s AND ISBN = %s
    """, (user_id, isbn))
    result = cursor.fetchone()
    conn.close()

    return jsonify({'inCart': bool(result)})


@app.route('/admin/book/<isbn>', methods=['PUT'])
def update_book(isbn):
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400

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


@app.route('/admin/book/<isbn>', methods=['DELETE'])
def delete_book(isbn):
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


if __name__ == '__main__':
    app.run(debug=True, port=3050, host='0.0.0.0')
