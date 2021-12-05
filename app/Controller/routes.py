from flask import Blueprint
from app.Model.experience_models import TechnicalElective, ResearchExperience
from config import Config
from flask_login import current_user, login_required
from app.Model.position_models import Position, Application
from app.Model.user_models import User
from flask import render_template, flash, redirect, url_for, request
from app import db
from flask_login import current_user, login_user, logout_user, login_required
from app.Controller.position_forms import CreatePositionForm, SortForm
from app.Controller.application_forms import ApplicationForm
from app.Controller.edit_forms import EditForm, EditTechnicalElectiveForm, EditResearchExperienceForm

import app.Model.user_models as user_models
from datetime import datetime

bp_routes = Blueprint('routes', __name__)
bp_routes.template_folder = Config.TEMPLATE_FOLDER #'..\\View\\templates'
bp_routes.static_folder = Config.STATIC_FOLDER

## FUTURE: With faculty, sort so faculty id is on top? Or only show faculty's post?
@bp_routes.route('/', methods=['GET', 'POST'])
@bp_routes.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    sForm = SortForm()
    positions = []
    
    if current_user.is_faculty() == False:
        if sForm.validate_on_submit():
            choice = sForm.sort_choice.data
            positions = list(eval(choice))
            #applied_positions = list(eval('reversed(sorted(positions, key=lambda position: position.id in [x.position_id for x in current_user.application_forms]))'))
                
        else:
            positions = Position.query.all()   
    else:
        positions = Position.query.all()

    return render_template('index.html', research_positions=positions, form=sForm)

def get_recommended_positions():
    display_positions = []
    positions = Position.query.all()
    for p in positions:
        fields = p.research_fields
        for field in current_user.interested_fields:
            if fields.count(field) > 0:
                display_positions.append(p)
                break
            
    return display_positions

@bp_routes.route('/position/<pos_id>', methods=['GET'])
@login_required
def display_position(pos_id):
    position = Position.query.filter_by(id=int(pos_id)).first()
    user = User.query.filter_by(id=position.faculty_id).first()
    return render_template('position.html', position=position, user=user)


@bp_routes.route('/view_applicants', methods=['GET'])
@login_required
def view_applicants():
    if not current_user.is_faculty():
        flash('Access Denied: not logged in as Faculty')
        return redirect(url_for('routes.index'))
    
    positions = Position.query.filter_by(faculty_id=current_user.id).all()
    
    return render_template('faculty_positions.html', positions=positions)


@bp_routes.route('/student/<student_id>', methods=['GET'])
@login_required
def display_applicant_info(student_id):
    if not current_user.is_faculty():
        flash('Access Denied: not logged in as Faculty')
        return redirect(url_for('routes.index'))
    
    student = User.query.filter_by(id=int(student_id)).first()
    
    return render_template('student.html', student=student)


@bp_routes.route('/apply/<pos_id>', methods=['GET', 'POST'])
@login_required
def apply(pos_id):
    if current_user.is_faculty():
        flash('Access Denied: You must be logged in as a student to apply for a position.')
        return redirect(url_for('routes.index'))

    position = Position.query.filter_by(id=int(pos_id)).first()
    if position is None:
        flash('Position not found')
        return redirect(url_for('routes.index'))

    application = Application.query.filter_by(position_id=int(pos_id), student_id=current_user.id).first() 
    if application is not None:
        flash(f'You have already applied for this position: {position.title}')
        return redirect(url_for('routes.index'))


    appForm = ApplicationForm()

    if appForm.validate_on_submit():
        application = Application(description=appForm.description.data, ref_name=appForm.ref_name.data,
                                    ref_email = appForm.ref_email.data, position_id=pos_id,
                                    student_id=current_user.id, student_name=f' {current_user.first_name} {current_user.last_name}'
                                    )
        application.save_to_db()
        flash('Application successfully submitted.')
        return redirect(url_for('routes.index'))
    
    return render_template('apply.html', form=appForm, pos_id=pos_id)


@bp_routes.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():

    if current_user.is_faculty():
        flash('Access Denied: You must be logged in as a student to apply for a position.')
        return redirect(url_for('routes.index'))

    user = User.query.filter_by(id = current_user.id).first()
    eForm = EditForm(obj=user)
    
    if eForm.validate_on_submit():
        eForm.populate_obj(user)
        db.session.commit()
        # save_to_db() ?
        
        flash("Account information has been edited.")
        return redirect(url_for('routes.index'))
        
    return render_template('edit.html', form=eForm)



@bp_routes.route('/technical_electives', methods=['GET'])
@login_required
def technical_electives():
    if current_user.is_faculty():
        flash('Access Denied: You must be logged in as a student to apply for a position.')
        return redirect(url_for('routes.index'))

    technical_electives = TechnicalElective.query.filter_by(student_id=current_user.id).all()
    return render_template('tech_electives.html', electives=technical_electives)


@bp_routes.route('/create_technical_elective', methods=['GET', 'POST'])
@login_required
def create_technical_elective():

    if current_user.is_faculty():
        flash('Access Denied: You must be logged in as a student to apply for a position.')
        return redirect(url_for('routes.index'))


    form = EditTechnicalElectiveForm()
    if form.validate_on_submit():
        technical_elective = TechnicalElective(course_num=form.course_num.data, course_title=form.course_title.data,
                                                course_prefix=form.course_prefix.data, course_description=form.course_description.data,
                                                student_id=current_user.id
                                                )
        technical_elective.save_to_db()
        flash("Technical Elective successfully added.")
        return redirect(url_for('routes.technical_electives'))
    
    return render_template('create_tech_elective.html', form=form)


@bp_routes.route('/research_experience', methods=['GET'])
@login_required
def research_experience():

    if current_user.is_faculty():
        flash('Access Denied: You must be logged in as a student to apply for a position.')
        return redirect(url_for('routes.index'))

    research_experience = ResearchExperience.query.filter_by(student_id=current_user.id).all()
    return render_template('prior_experiences.html', experiences=research_experience)


@bp_routes.route('/create_research_experience', methods=['GET', 'POST'])
@login_required
def create_research_experience():
    if current_user.is_faculty():
        flash('Access Denied: You must be logged in as a student to apply for a position.')
        return redirect(url_for('routes.index'))
    
    form = EditResearchExperienceForm()
    if form.validate_on_submit():

        research_experience = ResearchExperience(student_id=current_user.id, title=form.title.data,
                                                    company=form.company.data, description=form.description.data,
                                                    start_date=form.start_date.data, end_date=form.end_date.data)
        research_experience.save_to_db()
        flash('Research Experience succesfully added.')
        return redirect(url_for('routes.research_experience'))
    
    return render_template('create_prior_experience.html', form=form)



@bp_routes.route('/create_position', methods=['GET', 'POST'])
@login_required
def create_position():

    if not current_user.is_faculty():
        flash('Access Denied: not logged in as Faculty')
        return redirect(url_for('routes.index'))

    pform = CreatePositionForm()
    if pform.validate_on_submit():
        start_date  = datetime.strptime(pform.start_date.data, '%m/%d/%Y')
        end_date    = datetime.strptime(pform.end_date.data, '%m/%d/%Y')

        position = Position(title       = pform.title.data,
                            description = pform.description.data,
                            start_date  = start_date,
                            end_date    = end_date,
                            faculty_name= f'{current_user.first_name} {current_user.last_name}',
                            faculty_id  = current_user.id,
                            time_commitment          = int(pform.time_commitment.data),
                            required_qualifications  = pform.required_qualifications.data,
                            research_fields          = [x for x in pform.research_fields.data]
                            )

        position.save_to_db()
        flash('Position successfully created.')
        return redirect(url_for('routes.index'))

    return render_template('create.html', form=pform)
