from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os

app = Flask(__name__)
app.secret_key = "student_marks_secret"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "students.json")

SUBJECTS = ("Python", "Mathematics", "Physics", "English", "Computer")


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_data(students):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(students, file, indent=4)


def calculate_result(marks):
    total = sum(float(marks.get(subject, 0)) for subject in SUBJECTS)
    percentage = total / len(SUBJECTS)

    if percentage >= 75:
        grade = "Distinction"
    elif percentage >= 60:
        grade = "First Class"
    elif percentage >= 50:
        grade = "Second Class"
    elif percentage >= 35:
        grade = "Pass"
    else:
        grade = "Fail"

    return total, percentage, grade

@app.route("/search", methods=["GET", "POST"])
def search_student():
    roll_no = request.values.get("roll_no", "").strip()

    if not roll_no:
        flash("Please enter a roll number to search.")
        return redirect(url_for("dashboard"))

    students = load_data()

    student = next(
        (s for s in students if s["roll_no"].lower() == roll_no.lower()),
        None
    )

    if student is None:
        flash("No student found with this roll number.")
        return redirect(url_for("dashboard"))

    total, percentage, grade = calculate_result(student["marks"])

    return render_template(
        "search.html",
        student=student,
        total=total,
        percentage=percentage,
        grade=grade,
        subjects=SUBJECTS
    )

@app.route("/")
def dashboard():
    students = load_data()
    results = []

    for student in students:
        total, percentage, grade = calculate_result(student["marks"])
        results.append({
            "roll_no": student["roll_no"],
            "name": student["name"],
            "total": total,
            "percentage": percentage,
            "grade": grade
        })

    average = (
        sum(item["percentage"] for item in results) / len(results)
        if results else 0
    )
    topper = max(results, key=lambda item: item["percentage"]) if results else None

    return render_template(
        "index.html",
        students=results,
        total_students=len(students),
        average=average,
        topper=topper
    )


@app.route("/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        roll_no = request.form.get("roll_no", "").strip()
        name = request.form.get("name", "").strip()

        if not roll_no or not name:
            flash("Please enter roll number and name.")
            return redirect(url_for("add_student"))

        students = load_data()

        if any(s["roll_no"] == roll_no for s in students):
            flash("This roll number already exists.")
            return redirect(url_for("add_student"))

        marks = {}

        for subject in SUBJECTS:
            try:
                mark = float(request.form.get(subject, ""))
                if not 0 <= mark <= 100:
                    raise ValueError
                marks[subject] = mark
            except ValueError:
                flash("Enter valid marks between 0 and 100.")
                return redirect(url_for("add_student"))

        students.append({
            "roll_no": roll_no,
            "name": name,
            "marks": marks
        })

        save_data(students)
        flash("Student added successfully!")
        return redirect(url_for("dashboard"))

    return render_template("form.html", subjects=SUBJECTS, student=None)


@app.route("/edit/<roll_no>", methods=["GET", "POST"])
def edit_student(roll_no):
    students = load_data()
    student = next((s for s in students if s["roll_no"] == roll_no), None)

    if student is None:
        flash("Student not found.")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()

        if not name:
            flash("Name cannot be empty.")
            return redirect(url_for("edit_student", roll_no=roll_no))

        marks = {}

        for subject in SUBJECTS:
            try:
                mark = float(request.form.get(subject, ""))
                if not 0 <= mark <= 100:
                    raise ValueError
                marks[subject] = mark
            except ValueError:
                flash("Enter valid marks between 0 and 100.")
                return redirect(url_for("edit_student", roll_no=roll_no))

        student["name"] = name
        student["marks"] = marks
        save_data(students)
        flash("Student updated successfully!")
        return redirect(url_for("dashboard"))

    return render_template("form.html", subjects=SUBJECTS, student=student)


@app.route("/delete/<roll_no>", methods=["POST"])
def delete_student(roll_no):
    students = load_data()
    students = [s for s in students if s["roll_no"] != roll_no]
    save_data(students)
    flash("Student record deleted.")
    return redirect(url_for("dashboard"))


@app.route("/report")
def report():
    students = load_data()
    results = []

    for student in students:
        total, percentage, grade = calculate_result(student["marks"])
        results.append({
            "name": student["name"],
            "roll_no": student["roll_no"],
            "percentage": percentage,
            "grade": grade
        })

    results.sort(key=lambda item: item["percentage"], reverse=True)
    average = (
        sum(s["percentage"] for s in results) / len(results)
        if results else 0
    )

    return render_template("report.html", results=results, average=average)


if __name__ == "__main__":
    app.run(debug=True)
