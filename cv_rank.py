from lxml import html
from bs4 import BeautifulSoup
import re
import os

import decision_tree
# ### pdf to html

def rank(uid, job_skills):
    path = 'static/resumes'
    command = 'pdf2txt.py -o '+path+'/Resume_'+uid+'.html -t html '+path+'/Resume_'+uid+'.pdf'
    os.system(command)

# ### html to html code
    f = open('static/resumes/Resume_'+uid+'.html')
    txt = f.read()
    soup = BeautifulSoup(txt, features="lxml")

# ### collecting all font-size in span
    font_spans = [data for data in soup.select('span') if 'font-size' in str(data)]
    output = []
    for i in font_spans:
        tup = ()
        fonts = re.search(r'(?is)(font-size:)(.*?)(px)',str(i.get('style'))).group(2)
        tup = (int(fonts.strip()))
        #to get distinct font size
        if tup not in output:
            output.append(tup)

# ### get segment headings wrt font
    #first find average font-sizes used
    total = len(output)
    summation = sum(output)
    avg = summation/total
    #find segments if their font-size >= avg
    font_segments = []
    for i in font_spans:
        tup = ()
        fonts = re.search(r'(?is)(font-size:)(.*?)(px)',str(i.get('style'))).group(2)
        if int(fonts.strip()) >= avg:
            tup = (str(i.text).strip())
            font_segments.append(tup)

# ### get real segment headings
    segment_headings = []
#PI = ['principal', 'personal', 'summary', 'profile', 'statement', 'focus', 'program', 'development', 'profile', 'objective', 'overview', 'professional', 'introduction']
    E = ['educational', 'qualifications', 'academic', 'history']
    P = ['projects', 'works', 'involvement', 'job', 'experience']
    S = ['technical skills', 'skills', 'interpersonal skills', 'skillset' 'interests', 'additional skills']
#A = ['achievements', 'awards', 'accolades']
#EX = ['activities', 'activity', 'extra curricular', 'co-curricular', 'voluntary']
    H = [['principal', 'personal', 'summary', 'profile', 'statement', 'focus', 'program', 'development', 'profile', 'objective', 'overview', 'professional', 'introduction'],
    ['educational', 'education', 'qualifications', 'academic', 'history'],
    ['projects', 'works', 'involvement', 'job', 'experience'],
    ['technical skills', 'skills', 'interpersonal skills', 'interests', 'skillset', 'skills'],
    ['achievements', 'awards', 'accolades'],
    ['activities', 'activity', 'extra curricular', 'co-curricular', 'voluntary']]
    for heading in font_segments:
        i = heading.split()
        for j in i:
            j = j.lower()
            if any(j in s for s in H):
                segment_headings.append(heading)
                break

# ### get the segments
    var = []
    seg_dict = dict.fromkeys(segment_headings)
    for i in seg_dict:
        seg_dict[i] = []
    for i in font_spans:
        txt = (str(i.text).strip())
        if txt in segment_headings:
            var.append(txt)
        if len(var) != 0:
            heading = var[len(var)-1]
            seg_dict[heading].append(txt)

    for k in seg_dict:
        ks = k.lower()
        if any(ks in s for s in E):
        # ### get cgpa
            global cgpa
            cgpa = ''
            #dt= {}
            keywords = ['b.tech', 'btech', 'bachelor of technology', 'graduation', 'cse', 'computer science engineering']
            for i in seg_dict[k]:
                y = re.findall("(\d+\.\d+)(?=\s*cgpa)", i.lower())
                if len(y) != 0:
                    cgpa = ''.join(y)
                    break
            if cgpa == '':
                cgpa = '8.0'


        elif any(ks in s for s in S):
        # ### get skill_score
            global skill_score
            def techSkills(skillset):
                T_skills = 0
                for value in skillset:
                    for skills in seg_dict[k]:
                        if value in skills.lower():
                            T_skills=T_skills+3

                if T_skills>=2:
                    skill_score = 2.5
                elif T_skills==1:
                    skill_score = 2
                else:
                    skill_score = 1

                return skill_score
            def nonTechSkills(skill_set):
                s = 0
                TypeA = ['critical thinking', 'problem solving', 'observation', 'analysis', 'interpretation', 'evaluation', 'decision making', 'research']
                TypeB = ['quantitative ability', 'creativity', 'writing', 'tech', 'leadership', 'ability to handle data', 'mathematical skills']
                TypeC = ['oral communication', 'teamwork', 'organised']
                TypeD = ['smart', 'functional skills', 'finding information', 'media skills', 'technology proficiency']
                    
                A_count = 0
                B_count = 0
                C_count = 0
                D_count = 0
                for value in TypeA:
                    for skills in skill_set:
                        if value in skills.lower():
                            A_count=A_count+1
                for value in TypeB:
                    for skills in skill_set:
                        if value in skills.lower():
                            B_count=B_count+1
                for value in TypeC:
                    for skills in skill_set:
                        if value in skills.lower():
                            C_count=C_count+1
                for value in TypeD:
                    for skills in skill_set:
                        if value in skills.lower():
                            D_count=D_count+1

                ### Type A
                if A_count > 2:
                    s = s+4
                elif A_count==2:
                    s = s+3
                elif A_count==1:
                    s = s+2
                elif A_count==0:
                    s = s+0


                ### Type B
                if B_count > 2:
                    s = s+3
                elif B_count == 2:
                    s = s+2
                elif B_count == 1:
                    s = s+1
                elif B_count == 0:
                    s = s+0


                ### Type C
                if C_count >= 2:
                    s = s+2
                elif C_count == 1:
                    s = s+1
                elif C_count == 0:
                    s = s+0

                ### Type D
                if D_count >= 2:
                    s = s+1
                elif D_count == 1:
                    s = s+0.5
                elif D_count == 0:
                    s = s+0

                s=s/4
                return s

            T_skills = techSkills(job_skills)
            NT_skills = nonTechSkills(seg_dict[k])


            skill_score = T_skills+NT_skills

        elif any(ks in s for s in P):
        # ### get projects_score
            global projects_score
            def reqdProjects(projectset):
                T_projects = 0
                for value in projectset:
                    for i in seg_dict[k]:
                        if value in i.lower():
                            T_projects=T_projects+1
                            break

                if T_projects>2:
                    p=3
                elif T_projects==2:
                    p=2
                elif T_projects==1:
                    p=1
                elif T_projects==0:
                    p=0
                return p
            def totalProjects(projectset):
                length = 0
                for i in projectset:
                    if re.search(r'\d', i):
                        length = length+1
                if length>=4:
                    l=2
                elif length==3:
                    l=1.5
                elif length==2:
                    l=1
                elif length<=1:
                    l=0.5
                return l



            R_projects = reqdProjects(job_skills)
            T_projects = totalProjects(seg_dict[k])

            projects_score=R_projects+T_projects


    CGPA = float(cgpa)
    return_rank = decision_tree.rank_resume(CGPA, skill_score, projects_score)
    return return_rank
