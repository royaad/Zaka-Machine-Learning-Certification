import json, openai, Levenshtein, re, string, os
import numpy as np
from thefuzz import fuzz 
from openai.embeddings_utils import cosine_similarity

# Set OpenAI Key
openai.api_key = os.getenv("OPENAI_API_KEY")

def JSON_readfile(file_path):
    file = open(file_path)
    return json.load(file)

def save_dict2txt(filename, dict):
    with open(filename + ".txt", 'w') as f: 
        for key, value in dict.items(): 
            f.write('%s:\t\t%s\n' % (key, value))
            
def sort_str_words(sentence):
    words = [word.lower() for word in sentence.split()]
    if len(words) > 1:
      words.sort()
    return ' '.join(words)
      

def get_embedding(text, model="text-embedding-ada-002"):
    return openai.Embedding.create(input = [text], model=model)['data'][0]['embedding']

def relative_l1_distance(vect, ref):
    vect = np.array(vect)
    ref = np.array(ref)
    diff = np.abs(vect - ref)
    return np.sum(diff)

def norm_inv_distance(distance, max=21):
    if distance > max:
        return 0
    else:
        return 1 - distance/max

def geometric_mean(x, y):
    if x + y == 0:
        return 0
    else:
        return 2*(x * y)/(x + y)

def skill_list_match(skills_Job, skills_CV, threshold=80):
    matches = np.zeros((len(skills_Job), len(skills_CV)))
    re_punct = re.compile('[%s]' % re.escape(string.printable[62:]))
    for i, req_skill in enumerate(skills_Job):
        for j, skill in enumerate(skills_CV):
            if len(req_skill) > 3:
                cleaned_1 = re_punct.sub(' ', req_skill)
                cleaned_2 = re_punct.sub(' ', skill)
                match_1 = fuzz.partial_ratio(cleaned_1.lower(), cleaned_2.lower())
                match_2 = fuzz.ratio(cleaned_1.lower(), cleaned_2.lower())
                matches[i,j] = geometric_mean(match_1, match_2)
            else:
                cleaned_1 = re_punct.sub(' ', req_skill)
                cleaned_2 = re_punct.sub(' ', skill)
                matches[i,j] = fuzz.ratio(cleaned_1.lower(), cleaned_2.lower())
    matches = np.max(matches, axis = 1)
    matches = np.where(matches > threshold, 1, 0)
    return np.mean(matches)

def skills_score(skills_Job, skills_CV, score_mode):
    if score_mode.lower() == 'match':
        print('Skill Mode Match')
        return skill_list_match(skills_Job, skills_CV, 70)
    else:
        print('Skill Mode ADA')
        skills_Job = ' '.join(skills_Job)
        skills_CV = ' '.join(skills_CV)
        v1 = get_embedding(skills_Job)
        v2 = get_embedding(skills_CV)

        skills_cos = cosine_similarity(v1, v2)
        skills_l1 = relative_l1_distance(v1, v2)
        skills_l1 = norm_inv_distance(skills_l1)
        return geometric_mean(skills_cos, skills_l1)

def job_list_match(job_title_list, CV_breakdown_dict, sensitivity=100):
    if type(job_title_list) is not list:
        job_title_list = [job_title_list]
    re_punct = re.compile('[%s]' % re.escape(string.printable[62:]))
    match_list = []
    for i in job_title_list:
        for j in CV_breakdown_dict.keys():
            cleaned_i = re_punct.sub(' ', i)
            cleaned_j = re_punct.sub(' ', j)
            match = fuzz.partial_ratio(cleaned_i.lower(), cleaned_j.lower())
            if match >= sensitivity:
                match_list.append(j)
            else:
                cleaned_i = sort_str_words(cleaned_i)
                cleaned_j = sort_str_words(cleaned_j)
                match = fuzz.partial_ratio(cleaned_i.lower(), cleaned_j.lower())
                if match >= sensitivity:
                    match_list.append(j)
    return match_list

def relevant_years(job_list, CV_breakdown_dict):
    years = 0
    for job in job_list:
      years += CV_breakdown_dict[job]
    return years
  
def RELU(value, max):
    value = np.min([value, max])
    value = np.max([value, 0])
    if max == 0:
        return 1
    else:
        return value/max

def dict_2_txt(dict):
    titles = list(dict.keys())
    titles = [i+' ' for i in titles]
    years = np.int_(list(dict.values()))
    years = np.where(years == 0, 1, years)
    text = []
    for i, j in zip(titles, years):
        temp = i * j
        temp = temp.strip()
        text.append(temp)
    return ' '.join(text)

def list_2_txt(job_list, min_exp_years):
    if type(job_list) is not list:
        job_list = [job_list]
    repetitions = min_exp_years//len(job_list)
    repetitions = np.max([1, repetitions])
    job_list = [(i+' ')*repetitions for i in job_list]
    job_list = ' '.join(job_list)
    return job_list.strip()

def job_score_ada(job_title, job_experience):
    v1 = get_embedding(job_experience)
    v2 = get_embedding(job_title)
    
    jobs_cos = cosine_similarity(v1, v2)
    jobs_l1 = relative_l1_distance(v1, v2)
    jobs_l1 = norm_inv_distance(jobs_l1)
    return geometric_mean(jobs_cos, jobs_l1)

def CV_Ranker(JD_dict, CV_dict, Job_list, lang_mode='Strict', skills_mode='Match', job_mode='Match'):
  #Ranking for years of experience
  years_required = JD_dict['total_years_required']
  try: years_required = np.round(float(years_required))
  except: years_required = 0.0
  #Year Of Experience
  try: 
    YOE = CV_dict['total_years']
    try: YOE = float(YOE)
    except: YOE = 0.0
  except:
    YOE = 0.0
    print('Failed to read years of experience -> 0.0')
  #Step-like function
  if YOE < years_required:
    experience_score = 0
  else:
    experience_score = 1

  languages_required = JD_dict['languages']
  try:
    languages_spoken = CV_dict['languages']
    lang_levels = []
    for language in languages_required:
      try:
        lang_level = languages_spoken[language]
        try:
          lang_level = int(lang_level)
          if lang_level > 2:
            lang_levels.append(1)
          else:
            lang_levels.append(0)
        except:
          #Since he has the language by did not mention a level,
          #We will consider he passes.
          lang_levels.append(1)
      except:
        lang_levels.append(0)
    #2 modes for language ranking Strict / Relaxed
    if lang_mode.lower() == 'strict':
      lang_cond = np.prod(lang_levels)
    elif lang_mode.lower() == 'relaxed':
      lang_cond = np.sum(lang_levels)
      if lang_cond > 0.66*len(languages_required):
        lang_cond = 1
      else:
        lang_cond = 0
    else:
      raise Exception('This mode does not exist.')
  except:
    print('Failed to read languages')
    lang_cond = 0

  if lang_cond:
    print('CV will be considered for further study')
    try:
        skills_required = JD_dict['skills_required']
        skills_CV = CV_dict['skills']
        if skills_CV:
            skill_score = skills_score(skills_required, skills_CV, skills_mode)
        else:
            print('Skills list is empty -> CV will be disregarded -> skill_score = 0')
            skill_score = 0
    except:
        print('Skills reading failed -> skill_score = 0')
        skill_score = 0
    try:
      job_experience = CV_dict['breakdown_experience']
      if Job_list is not None:
          job_title = Job_list
      else:
          job_title = JD_dict['job_title']
      min_exp_years = JD_dict['total_years_required']
      if job_experience:
          job_matches = job_list_match(job_title, job_experience)
          relevant_exp_years = relevant_years(job_matches, job_experience)
          if experience_score or relevant_exp_years:
              if job_mode.lower() == "match":
                  print('Job Mode Match')
                  relevance_score = RELU(relevant_exp_years, min_exp_years)
                  job_score = relevance_score
              elif job_mode.lower() == 'ada':
                  print('Job Mode ADA')
                  job_title_str = list_2_txt(job_title, min_exp_years)
                  job_experience_str = dict_2_txt(job_experience)
                  job_score = job_score_ada(job_title_str, job_experience_str)
              else:
                  print('Job Mode ADAMa')
                  job_title_str = list_2_txt(job_title, min_exp_years)
                  job_experience_str = dict_2_txt(job_experience)
                  job_score = job_score_ada(job_title_str, job_experience_str)
                  relevance_score = RELU(relevant_exp_years, min_exp_years)
                  job_score = (1 + relevance_score)*job_score
          else:
              print("Years of experience not met -> job score = 0")
              job_score = 0
      else:
        print('Experience list is empty -> CV will be disregarded -> job_score = 0')
        job_score = 0
    except:
      print('Experience reading failed -> total_score = 0')
      job_score = 0
    
    if job_mode.lower() == 'adama':
        total_score = skill_score + job_score
    else:
        total_score = geometric_mean(skill_score, job_score)
  else:
    print('CV will be ignored')
    total_score = 0
  
  return total_score