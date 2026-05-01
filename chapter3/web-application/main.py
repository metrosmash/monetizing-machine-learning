#!/usr/bin/env python
from flask import Flask, render_template, request
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io, base64
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

# Default traveler constants
DEFAULT_EMBARKED = 'Southampton'
DEFAULT_FARE = 33
DEFAULT_AGE = 30
DEFAULT_GENDER = 'Female'
DEFAULT_TITLE = 'Mrs.'
DEFAULT_CLASS = 'Second'
DEFAULT_CABIN = 'C'
DEFAULT_SIBSP = 0
DEFAULT_PARCH = 0

# Global state
average_survival_rate = 0
lr_model = LogisticRegression()

app = Flask(__name__)
app.secret_key = 'titanic-secret-key'


def startup():
    """Load data and train model at startup."""
    global average_survival_rate, lr_model

    titanic_array = np.genfromtxt('titanic3.csv', delimiter=',')
    average_survival_rate = np.mean([item[0] for item in titanic_array]) * 100

    X = [item[1:] for item in titanic_array]
    y = [item[0] for item in titanic_array]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.5, random_state=42
    )
    lr_model.fit(X_train, y_train)


# Run startup when app initializes (Flask 2.x compatible)
with app.app_context():
    startup()


@app.route("/", methods=['POST', 'GET'])
def submit_new_profile():
    model_plot = ''

    if request.method == 'POST':
        selected_embarked = request.form['selected_embarked']
        selected_fare     = request.form['selected_fare']
        selected_age      = request.form['selected_age']
        selected_gender   = request.form['selected_gender']
        selected_title    = request.form['selected_title']
        selected_class    = request.form['selected_class']
        selected_cabin    = request.form['selected_cabin']
        selected_sibsp    = request.form['selected_sibsp']
        selected_parch    = request.form['selected_parch']

        # Core numeric features
        age    = int(selected_age)
        isfemale = 1 if selected_gender == 'Female' else 0
        sibsp  = int(selected_sibsp)
        parch  = int(selected_parch)
        fare   = int(selected_fare)

        # Port of embarkation — FIX: was hardcoding embarked_Q=1 regardless of selection
        embarked_Q       = 0
        embarked_S       = 0
        embarked_Unknown = 0
        embarked_nan     = 0
        if selected_embarked[0] == 'Q':
            embarked_Q = 1
        elif selected_embarked[0] == 'S':
            embarked_S = 1
        else:
            embarked_Unknown = 1

        # Passenger class — FIX: was never setting these to 1
        pclass_Second = 0
        pclass_Third  = 0
        pclass_nan    = 0
        if selected_class == 'Second':
            pclass_Second = 1
        elif selected_class == 'Third':
            pclass_Third = 1

        # Title — FIX: Rev was incorrectly setting title_Master=1
        title_Master  = 0
        title_Miss    = 0
        title_Mr      = 0
        title_Mrs     = 0
        title_Rev     = 0
        title_Unknown = 0
        title_nan     = 0
        title_map = {
            'Master.': 'title_Master',
            'Miss.':   'title_Miss',
            'Mr.':     'title_Mr',
            'Mrs.':    'title_Mrs',
            'Rev.':    'title_Rev',
            'Unknown': 'title_Unknown',
        }
        if selected_title in title_map:
            locals()[title_map[selected_title]]  # resolve name
        # Use explicit assignment to avoid locals() mutation issues
        if selected_title == 'Master.': title_Master = 1
        elif selected_title == 'Miss.': title_Miss = 1
        elif selected_title == 'Mr.':   title_Mr = 1
        elif selected_title == 'Mrs.':  title_Mrs = 1
        elif selected_title == 'Rev.':  title_Rev = 1
        elif selected_title == 'Unknown': title_Unknown = 1

        # Cabin
        cabin_B = cabin_C = cabin_D = cabin_E = 0
        cabin_F = cabin_G = cabin_T = cabin_Unknown = cabin_nan = 0
        cabin_map = {
            'B': 'cabin_B', 'C': 'cabin_C', 'D': 'cabin_D',
            'E': 'cabin_E', 'F': 'cabin_F', 'G': 'cabin_G',
            'T': 'cabin_T', 'Unknown': 'cabin_Unknown',
        }
        if selected_cabin == 'B': cabin_B = 1
        elif selected_cabin == 'C': cabin_C = 1
        elif selected_cabin == 'D': cabin_D = 1
        elif selected_cabin == 'E': cabin_E = 1
        elif selected_cabin == 'F': cabin_F = 1
        elif selected_cabin == 'G': cabin_G = 1
        elif selected_cabin == 'T': cabin_T = 1
        elif selected_cabin == 'Unknown': cabin_Unknown = 1

        # Build feature vector matching training data format
        user_passenger = [[
            age, sibsp, parch, fare, isfemale,
            pclass_Second, pclass_Third, pclass_nan,
            cabin_B, cabin_C, cabin_D, cabin_E, cabin_F, cabin_G, cabin_T, cabin_Unknown, cabin_nan,
            embarked_Q, embarked_S, embarked_Unknown, embarked_nan,
            title_Master, title_Miss, title_Mr, title_Mrs, title_Rev, title_Unknown, title_nan
        ]]

        Y_pred = lr_model.predict_proba(user_passenger)
        survival_pct = Y_pred[0][1] * 100

        # Generate chart
        fig, ax = plt.subplots(figsize=(6, 4))
        objects = ('Average Survival Rate', 'Your Traveler')
        y_pos = np.arange(len(objects))
        ax.bar(y_pos, [average_survival_rate, survival_pct],
               align='center', color=['gray', 'steelblue'], alpha=0.7)
        ax.set_xticks(y_pos)
        ax.set_xticklabels(objects)
        ax.axhline(average_survival_rate, color='red', linestyle='--', linewidth=1)
        ax.set_ylim([0, 100])
        ax.set_ylabel('Survival Probability (%)')
        ax.set_title(f'Your Traveler: {survival_pct:.1f}% Chance of Surviving!')
        plt.tight_layout()

        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close(fig)
        # Pass base64 string only — template renders the <img> tag safely
        model_plot = base64.b64encode(img.getvalue()).decode()

        return render_template('index.html',
            model_plot=model_plot,
            selected_embarked=selected_embarked,
            selected_fare=selected_fare,
            selected_age=selected_age,
            selected_gender=selected_gender,
            selected_title=selected_title,
            selected_class=selected_class,
            selected_cabin=selected_cabin,
            selected_sibsp=selected_sibsp,
            selected_parch=selected_parch)
    else:
        return render_template('index.html',
            model_plot='',
            selected_embarked=DEFAULT_EMBARKED,
            selected_fare=DEFAULT_FARE,
            selected_age=DEFAULT_AGE,
            selected_gender=DEFAULT_GENDER,
            selected_title=DEFAULT_TITLE,
            selected_class=DEFAULT_CLASS,
            selected_cabin=DEFAULT_CABIN,
            selected_sibsp=DEFAULT_SIBSP,
            selected_parch=DEFAULT_PARCH)


if __name__ == '__main__':
    app.run(debug=False)
