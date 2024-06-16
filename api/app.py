from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, auth, firestore


# instances
app = Flask(__name__)
cred = credentials.Certificate("src/serviceAccountKey.json")
# initialize firebase  app with the service account key
firebase_admin.initialize_app(cred)

db = firestore.client()



# loading model
model = joblib.load('../models/fraud_model_cycle1.joblib')


# Predict fraud
@app.route('/fraud/predict', methods=['POST'])
def churn_predict():
    test_json = request.get_json()
   
    if test_json: # there is data
        if isinstance(test_json, dict): # unique example
            test_raw = pd.DataFrame(test_json, index=[0])
            
        else: # multiple example
            test_raw = pd.DataFrame(test_json, columns=test_json[0].keys())
            
        # Instantiate Rossmann class
        pipeline = Fraud()
        
        # data cleaning
        df1 = pipeline.data_cleaning(test_raw)
        
        # feature engineering
        df2 = pipeline.feature_engineering(df1)
        
        # data preparation
        df3 = pipeline.data_preparation(df2)
        
        # prediction
        df_response = pipeline.get_prediction(model, test_raw, df3)
        
        return df_response
        
        
    else:
        return Reponse('{}', status=200, mimetype='application/json')



# Update a document in Firestore
def update_document(collection, document_id, update_data):
    db = firestore.client()
    doc_ref = db.collection(collection).document(document_id)
    doc_ref.update(update_data)
    print('Document updated successfully!')


# Transfer Money Function
def transfer_money(sender_email, recipient_email, amount):
    sender_ref = db.collection('users').where('email', '==', sender_email).limit(1).get()
    recipient_ref = db.collection('users').where('email', '==', recipient_email).limit(1).get()

    if len(sender_ref) == 0:
        return 'Sender not found'
    if len(recipient_ref) == 0:
        return 'Recipient not found'

    sender_doc = sender_ref[0]
    recipient_doc = recipient_ref[0]

    sender_data = sender_doc.to_dict()
    recipient_data = recipient_doc.to_dict()

    sender_balance = sender_data.get('balance', 0)
    recipient_balance = recipient_data.get('balance', 0)

    if sender_balance < amount:
        return 'Insufficient balance'

    # Update sender's balance
    sender_new_balance = sender_balance - amount
    db.collection('users').document(sender_doc.id).update({'balance': sender_new_balance})

    # Update recipient's balance
    recipient_new_balance = recipient_balance + amount
    db.collection('users').document(recipient_doc.id).update({'balance': recipient_new_balance})

    return 'Transfer successful'

@app.route('/transfer', methods=['POST'])
def transfer():
    data = request.json
    if data == {}:
        return jsonify({'error': 'must not be empty'}), 400

    sender_uid = data.get('sender_uid')  # Assuming the sender's UID is provided in the request
    sender_email = data.get('sender_email')
    recipient_email = data.get('recipient_email')
    amount = data.get('amount')

     # Retrieve the authenticated user's UID
    authenticated_uid = request.headers.get('X-UID')  # Assuming the authenticated UID is included in the request headers

    # Verify that the provided sender's UID matches the authenticated UID
    if sender_uid != authenticated_uid:
        return jsonify({'error': 'Unauthorized access'}), 401

    # Check if sender exists and retrieve sender's email
    sender_ref = db.collection('users').document(sender_uid).get()
    if not sender_ref.exists:
        return jsonify({'error': 'Sender not found'}), 404
    sender_data = sender_ref.to_dict()
    sender_email_from_db = sender_data.get('email')

    # Verify that the provided sender email matches the email stored in the database
    if sender_email_from_db != sender_email:
        return jsonify({'error': 'Sender email does not match'}), 400

    # Continue with the transfer process
    # Call transfer_money function with sender_email, recipient_email, and amount
    result = transfer_money(sender_email, recipient_email, amount)

    return jsonify({'result': result})


if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)

# /*
# Firebase Operations 
# */ 
# Create a new document in Firestore
# def create_document(collection, document_data):
#     db = firestore.client()
#     doc_ref = db.collection(collection).document()
#     doc_ref.set(document_data)
#     print('Document created with ID:', doc_ref.id)


# Usage example
# create_document('users', {'name': 'John Doe', 'email': 'johndoe@example.com'})

# Read a document from Firestore
# def read_document(collection, document_id):
#     db = firestore.client()
#     doc_ref = db.collection(collection).document(document_id)
#     document = doc_ref.get()
#     if document.exists:
#         print('Document data:', document.to_dict())
#     else:
#         print('No such document!')

# Usage example
# read_document('users', 'document_id123')



# Usage example
# update_document('users', 'document_id123', {'name': 'Jane Smith'})


# Delete a document from Firestore
# def delete_document(collection, document_id):
#     db = firestore.client()
#     doc_ref = db.collection(collection).document(document_id)
#     doc_ref.delete()
#     print('Document deleted successfully!')

# Usage example
# delete_document('users', 'document_id123')