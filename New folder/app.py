from flask import Flask, render_template, request, redirect, url_for, flash, session
from cloudant.client import Cloudant 
import os
import random
import datetime
import smtplib

import decision_tree
import cv_rank 
import cb

app = Flask(__name__)
app.secret_key = 'dont tell anyone'

client = Cloudant.iam(username, apikey) 
client.connect()
db1 = client['users']
jobs = client['jobs']
dbTQ = client['tech_que']
dbAQ = client['apt_que']

UPLOAD_FOLDER = 'static/resumes/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
user_list = []
global seq_list

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


@app.route('/')
def Home():
	return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def Login():
	if request.method == 'POST':
		userDetails = request.form
		email = userDetails['email']
		password = userDetails['password']

		uid = 'users:'+email
		cid = 'company:'+email

		if uid in db1:
			if db1[uid]['password'] == password:
				session['logged_in'] = True
				session['user_id'] = uid
				session['user_name'] = db1[uid]['name']
				return redirect(url_for('ApplicantHome'))
			else:
				return render_template('login.html', error='Incorrect Password !')
		elif cid in db1:
			if db1[cid]['password'] == password:
				company_name = db1[cid]['company_name']
				l = []
				for i in company_name.split(' '):
					l.append(i[0])
				partitioned_key = ''.join(l)
				session['logged_in'] = True
				session['company_id'] = cid
				session['company_name'] = partitioned_key
				return redirect(url_for('CompanyHome'))
			else:
				return render_template('login.html', error='Incorrect Password !')
		else:
			return render_template('login.html', error='This Email Does Not Exists !')

	if session.get('user_name'):
		return redirect(url_for('ApplicantHome'))
	elif session.get('company_name'):
		return redirect(url_for('CompanyHome'))
	else:
		return render_template('login.html')

@app.route('/registration', methods=['GET', 'POST'])
def Registration():
	if request.method == 'POST':
		userDetails = request.form
		type = userDetails.get('select')
		if type == '1':
			name = userDetails['aname']
			email = userDetails['aemail']
			gender = userDetails['agender']
			password = userDetails['apassword']
			profile_photo = request.files['photo']
			uid = 'users:'+email
			if uid in db1:
				return render_template('registration.html', error='User already exists !')
			else:
				new_doc = db1.create_document({'_id': uid, 'name': name, 'password': password, 'gender': gender})	
				if new_doc.exists():
					session['logged_in'] = True
					session['user_id'] = uid
					session['user_name'] = db1[uid]['name']
					return redirect(url_for('ApplicantHome'))
		else:
			name = userDetails['cname']
			des = userDetails['cdetails']
			email = userDetails['cemail']
			password = userDetails['cpassword']
			company_logo = request.files['logo']
			cid = 'company:'+email
			if cid in db1:
				return render_template('registration.html', error='User already exists !')
			else:
				new_doc = db1.create_document({'_id': cid, 'company_name': name, 'des': des, 'password': password})	
				if new_doc.exists():
					company_name = db1[cid]['company_name']
					l = []
					for i in company_name.split(' '):
						l.append(i[0])
					partitioned_key = ''.join(l)
					session['logged_in'] = True
					session['company_id'] = cid
					session['company_name'] = partitioned_key
					return redirect(url_for('CompanyHome'))
	return  render_template('registration.html')

@app.route('/forgotpassword', methods=['GET','POST'])
def ForgotPassword():
	if request.method == 'POST':
		userDetails = request.form
		email = userDetails['email']
		password = userDetails['password']
		id = 'users:'+email
		if id in db1:
			db1[id]['password'] = password
			db1[id].save()
			return redirect(url_for('Login'))
		else:
			return render_template('forgotpassword.html', error='User does not exist !')
	return render_template('forgotpassword.html')

@app.route('/logout')
def Logout():
	session.pop('logged_in', None)
	if session.get('user_name'):
		session.pop('user_name', None)	
		session.pop('user_id', None)
	if session.get('company_name'):
		session.pop('company_name', None)
		session.pop('company_id', None)
	return redirect(url_for('Login'))




@app.route('/applicantHomePage')
def ApplicantHome():
	if session.get('logged_in'):
		if session.get('user_name'):		
			user_name = session.get('user_name', None)
			user_id = session.get('user_id', None)
			try:
				results = jobs.get_query_result({'status': 'success'})
				companies = db1.partitioned_all_docs('company', include_docs=True)
			except ConnectionError:
				return 'There occurred some problem. Please try later.'
			return render_template('applicant/applicant.html', results=results, companies=companies['rows'], user=user_name, uid = user_id, var='apply')
		else:
			return 'you are not logged in'
	else:
		return 'you are not logged in'

@app.route('/already applied jobs')
def AppliedJobs():
	if session.get('logged_in'):
		if session.get('user_name'):		
			user_name = session.get('user_name', None)
			user_id = session.get('user_id', None)
			try:
				results = jobs.get_query_result({'status': 'success'})
				companies = db1.partitioned_all_docs('company', include_docs=True)
				userInfo = db1[user_id]
			except ConnectionError:
				return 'There occurred some problem. Please try later.'
			return render_template('applicant/applicant.html', results=results, companies=companies['rows'], userInfo=userInfo, user=user_name, uid = user_id, var='applied')
		else:
			return 'you are not logged in'
	else:
		return 'you are not logged in'

@app.route('/companyHomePage', methods=['GET', 'POST'])
def CompanyHome():
	if session.get('logged_in'):
		if session.get('company_name'):
			user_id = session.get('company_id', None)
			company_name = session.get('company_name', None)
			part_id = '^'+company_name+':'
			details = db1[user_id]
			try:
				results = db1.get_partitioned_query_result('users', {'jobs': {'$elemMatch': {'$regex': part_id}}})
				jobtitles = jobs.get_partitioned_query_result(company_name, {'status': 'success'})
			except ConnectionError:
				return 'There occurred some problem. Please try later.'			
			return render_template('company/company.html', results=results, details=details, jobs=jobtitles)
		else:
			return 'you are not logged in'	
	else:
		return 'you are not logged in'

@app.route('/companyHomePage with job title=<jid>', methods=['GET', 'POST'])
def CompanyHomeWithJobId(jid):
	if session.get('logged_in'):
		if session.get('company_name'):
			user_id = session.get('company_id', None)
			company_name = session.get('company_name', None)
			part_id = '^'+company_name+':'
			details = db1[user_id]
			jobtitle = jobs[company_name+':'+jid]
			try:
				results = db1.get_partitioned_query_result('users', {'jobs': {'$elemMatch': {'$regex': part_id}}})
				jobtitles = jobs.get_partitioned_query_result(company_name, {'status': 'success'})
			except ConnectionError:
				return 'There occurred some problem. Please try later.'			
			return render_template('company/company.html', results=results, details=details, jobs=jobtitles, job=jobtitle)
		else:
			return 'you are not logged in'	
	else:
		return 'you are not logged in'

@app.route('/hire the applicant for the job id=<jid>', methods=['GET', 'POST'])
def HiringMail(jid):
	if request.method == 'POST':
		user_id = request.form['user']
		company_name = jobs[jid]['company']
		job_title = jobs[jid]['title']
		html_content = """\
		<html>
		<head></head>
		<body>
		<h2>Warm wishes !</h2><br><br>
		<p>This is to inform you that you have been selected by the company <b>'""" + company_name +"""''</b>  for the job profile - <b>'""" + job_title +"""'</b>.<br><br></p>
		</body>
		</html>
		"""
		receiver = user_id[6:]
		message = MIMEMultipart()
		message['From'] = sender_email
		message['To'] = receiver
		message['Subject'] = "testing mail"
		part2 = MIMEText(html_content, 'html')
		message.attach(part2)
 
		session = smtplib.SMTP('smtp.gmail.com', 587)
		session.starttls()
		session.login(sender_email, sender_password)
		text = message.as_string()
		sentMail = session.sendmail(sender_email, receiver, text)
		session.quit()
		doc = db1[user_id]
		doc[jid]['status'] = 'Hired'
		doc.save()
		return redirect(url_for(CompanyHome))





@app.route('/applying for job id=<jid>')
def Apply(jid):
	global user_list
	user_list = []
	return redirect(url_for('Instructions', jid=jid))

@app.route('/before you start for job id=<jid>')
def Instructions(jid):
	return render_template('applicant/instruction.html', jid=jid)

@app.route('/upload your resume for job id=<jid>', methods=['GET', 'POST'])
def Upload(jid):
	if request.method == 'POST' and 'doc' in request.files:
		file = request.files['doc']
		user_id = session.get('user_id', None)
		name = user_id[6:].rsplit('@')[0]
		file.filename = "Resume_"+name+".pdf"
		file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
		skills = jobs[jid]['skills']
		return_rank = cv_rank.rank(name, skills)
		user_list.append(return_rank)
		return redirect(url_for('Test', type='Aptitude', jid=jid))
	return render_template('applicant/uploadresume.html', job=jid.rsplit(':')[1])

@app.route('/test your <type> Skills for job id=<jid>', methods=['GET', 'POST'])
def Test(type, jid):
	if request.method == 'POST':
		marks = 0
		if jobs[jid][type] == 'self':
			part_id = jid.rsplit(':')[0]+':'
		elif jobs[jid][type] == 'db':
			part_id = 'all:'
		skill_list = jobs[jid]['skills']
		skill_ids = get_key(skill_list)
		if not skill_ids:
			skill_ids = ['python']
		for i in range(1,11):
			if request.form.get('que'+str(i)):
				question = request.form.get('que'+str(i))
				checked = request.form.get('ans'+str(i))
				if type == 'Aptitude':
					correct = dbAQ[part_id+question]['correct']
				else:
					for i in skill_ids:
						part_id = 'all_'+i+':'
						if part_id+question in dbTQ:
							correct = dbTQ[part_id+question]['correct']
							break
				if checked == correct:
					marks = marks+1
				else:
					marks = marks+0
		user_id = session.get('user_id', None)
		user_list.append(marks)
		if type == 'Aptitude':
			return redirect(url_for('Test', type='Technical', jid=jid))
		else:
			try:
				cv_score = user_list[0]
				passing_marks = user_list[1]+user_list[2]
			except IndexError:
				passing_marks = 10
				cv_score = 3
			if passing_marks >= 14:
				if cv_score > 5:
					return redirect(url_for('Interview', jid=jid))	
				else:
					return redirect(url_for('Fail', jid=jid, state='fail'))
			else:
				return redirect(url_for('Fail', jid=jid, state='fail'))
		
	if jobs[jid][type] == 'self':
		part_id = jid.rsplit(':')[0]
	elif jobs[jid][type] == 'db':
		part_id = 'all'

	if type == 'Technical':
		skill_list = jobs[jid]['skills']
		skill_ids = get_key(skill_list)
		if not skill_ids:
			skill_ids = ['python']
		ques = []
		for i in skill_ids:
			partKey = 'all_'+i
			try:
				ques.extend(dbTQ.partitioned_all_docs(partKey, include_docs=True)['rows'])
				random.shuffle(ques)
			except ConnectionError:
				return 'There occurred some problem. Please try later.'
	else:
		try:
			ques = dbAQ.partitioned_all_docs(part_id, include_docs=True)['rows']
		except ConnectionError:
			return 'There occurred some problem. Please try later.'			
	results = random.sample(ques, 10)
	return render_template('applicant/answer.html', results=results, var=type)

@app.route("/give your interview for job id=<jid>")
def Interview(jid):
	global global_skill_ids
	skill_list = jobs[jid]['skills']
	global_skill_ids = get_key(skill_list)
	user_id = session.get('user_id', None)
	user_name = db1[user_id]['name']
	gender = db1[user_id]['gender']
	hour = datetime.datetime.now().hour
	if 0 <= hour < 12:
		wish = 'Good Morning '+user_name+' !'
	elif 12 <= hour < 17:
		wish = 'Good Afternoon '+user_name+' !'
	else:
		wish = 'Good Evening '+user_name+' !'
	return render_template('applicant/chatbot.html', wish=wish, jid=jid, gender=gender)

seq_list = ['0']
@app.route("/get")
def get_bot_response():
	userText = request.args.get('msg')
	if len(seq_list) == 0:
		seq_list.append('0')
	if len(seq_list) == 1:
		user_name = session.get('user_name', None)
		cb.test(global_skill_ids, user_name.split(' ')[0])

	res = cb.chat(userText, int(seq_list[len(seq_list)-1]))
	if res.rsplit(':')[0] == '4':
		seq_list.append(res.rsplit(':')[0])
		return res.rsplit(':')[1]
	if res.rsplit(':')[0] == '5':
		seq_list.clear()
		return 'over'
	else:
		seq_list.append(res.rsplit(':')[0])
		return res.rsplit(':')[1]

@app.route('/successfully <type>')
def Success(type):
	return render_template('thankyou.html', type=type)

@app.route('/result of applying for the job with id=<jid> is <state>')
def Fail(jid, state):
	if state == 'fail':
		return render_template('applicant/fail.html')
	else:
		interview = cb.get_int_skills_and_marks()
		interview_score = interview.pop(0)
		exp = interview.pop(0)
		state = False
		reqd_exp = int(jobs[jid]['experience'])
		try:
			cv_score = user_list[0]
			apt_marks = user_list[1]
			tech_marks = user_list[2]
		except IndexError:
			return render_template('applicant/fail.html')
		overall_marks = cv_score+apt_marks+tech_marks+interview_score
		if interview[0] != 'out':
			if overall_marks >= 30:
				if exp == '0 - 1 year':
					if reqd_exp <= 1:
						state = True
					else:
						if overall_marks >= 35:
							state = True
							interview.insert(0, 'A freshee but ->')

				elif exp == '2 - 4 years':
					if 2 <= reqd_exp <= 4:
						state = True
					elif reqd_exp > 4:
						if overall_marks >= 35:
							state = True
							interview.insert(0, 'A less experienced applicant but ->')
				else:
					if reqd_exp >= 5:
						state = True

		user_id = session.get('user_id', None)
		doc = db1[user_id]
		if state:
			doc[jid] = {'overall_marks': overall_marks, 'cv_score': user_list[0], 'apt_marks': user_list[1], 'tech_marks': user_list[2], 'experience': exp, 'interview_score': interview_score, 'interview_skills': interview, 'status': 'Applied'}
		else:
			doc[jid] = {'overall_marks': overall_marks, 'cv_score': user_list[0], 'apt_marks': user_list[1], 'tech_marks': user_list[2], 'experience': exp, 'interview_score': interview_score, 'interview_skills': interview, 'status': 'Disqualified'}
		doc.list_field_append(doc, 'jobs', jid)
		doc.save()
		user_list.clear()
		jdoc = jobs[jid]
		jdoc.list_field_append(jdoc, 'users', user_id)
		jdoc.save()

		return redirect(url_for('Success', type='recorded'))






@app.route('/creating job profile', methods=['GET', 'POST'])
def AddJobProfile():
	if request.method == 'POST':
		jobDetails = request.form
		job_experience = jobDetails['experience']
		job_title = jobDetails['title']
		job_skills = jobDetails.getlist('skills')
		extra = jobDetails.get('extra')

		company_name = session.get('company_name', None)
		user_id = session.get('company_id', None)
		company = db1[user_id]['company_name']

		jid = ':'.join((company_name, job_title))
		new_doc = jobs.create_document({'_id': jid, 'title': job_title, 'skills': job_skills, 'experience': job_experience, 'extra': extra, 'company': company})
		if new_doc.exists():
			return redirect(url_for('Que', var='all', type='Aptitude', jid=jid))		

skill_dict = {'java': ['java', 'java programming language'], 
              'php': ['php', 'hypertext preprocessor', 'web development', 'phpmysql', 'full stack developer'], 
              'python': ['python', 'ml', 'ai', 'ai/ml', 'artificial intelligence', 'machine learning'], 
              'app': ['app development', 'android development', 'swift', 'kotlin', 'flutter', 'dart'], 
              'dbms': ['dbms', 'database management system', 'backend', 'mysql', 'sql', 'mongodb'], 
              'hcss': ['html/css', 'html', 'css', 'frontend developer', 'front-end developer', 'full stack developer'], 
              'c': ['c', 'c++', 'c#', 'unity', '.net', 'c/c++'],
              'js': ['js', 'javascript', 'full stack developer', 'ajax', 'frontend developer', 'front-end developer']
             }
    
def get_key(val_list):
	key_list = []
	for val in val_list:
		for key, value in skill_dict.items():
			if val.lower() in value:
				key_list.append(key)
	return list(set(key_list))

@app.route('/<var> <type> Questions for job id=<jid>')
def Que(var, type, jid):
	company_name = session.get('company_name', None)
	isCreated = False
	if type == 'Technical':
		skill_list = jobs[jid]['skills']
		skill_ids = get_key(skill_list)
		if not skill_ids:
			skill_ids = ['python']
		compPartKey = company_name
		results = []
		try:
			r = dbTQ.partitioned_all_docs(compPartKey, include_docs=True)
			if r['total_rows'] != 0:
				isCreated = True

			if(var == 'created'):
				results = r['rows']
			else:
				for i in skill_ids:
					partKey = var+'_'+i
					results.extend(dbTQ.partitioned_all_docs(partKey, include_docs=True)['rows'])
		except ConnectionError:
			return 'There occurred some problem. Please try later.'			

	elif type == 'Aptitude':
		skill_list = []
		try:
			r = dbAQ.partitioned_all_docs(company_name, include_docs=True)
			if r['total_rows'] != 0:
				isCreated = True

			if(var == 'created'):
				results = r['rows']
			else:
				results = dbAQ.partitioned_all_docs(var, include_docs=True)['rows']	
		except ConnectionError:
			return 'There occurred some problem. Please try later.'			

	random.shuffle(results)
	return render_template('company/queset.html', results=results, type=type, ques=var, skills=skill_list, isCreated=isCreated, jid=jid)
	
@app.route('/add <type> question <no> for job id=<jid>', methods=['GET', 'POST'])
def AddQuestion(type, no, jid):
	if request.method == 'POST':
		data = request.form
		que = data['question']
		opt1 = data['option1']
		opt2 = data['option2']
		opt3 = data['option3']
		opt4 = data['option4']
		cid = data['correct']
		correct = data[cid]

		company_name = session.get('company_name', None)
		if type=='Technical':
			qid = ':'.join((company_name, que))
			new_doc = dbTQ.create_document({'_id': qid, 'que': que, 'opt1': opt1, 'opt2': opt2, 'opt3': opt3, 'opt4': opt4, 'correct': correct})	
		else:
			qid = ':'.join((company_name, que))
			new_doc = dbAQ.create_document({'_id': qid, 'que': que, 'opt1': opt1, 'opt2': opt2, 'opt3': opt3, 'opt4': opt4, 'correct': correct})	

		if new_doc.exists():
			if no == '10':
				return redirect(url_for('Que', var='created', type=type, jid=jid))
			else:
				next = int(no)+1
				no = str(next)
				return redirect(url_for('AddQuestion', type=type, no=no, jid=jid))

	return render_template('company/create_que.html', type=type, no=no)

@app.route('/selected <type> Question Set is <var> for job id=<jid>')
def QueSet(type, var, jid):
	jobs[jid][type] = var
	jobs[jid].save()
	if type == 'Aptitude':
		return redirect(url_for('Que', var='all', type='Technical', jid=jid))
	else:
		jobs[jid]['status'] = 'success'
		jobs[jid].save()
		return redirect(url_for('Success', type='created'))
 
if __name__ == "__main__":
    app.run(debug=True)