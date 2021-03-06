import calendar
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from TwitterAPI import TwitterAPI
from django.shortcuts import render
from assignment.forms import UserForm
from django.contrib.auth import logout
from assignment.models import Album, User
from django.core.mail import send_mail

consumer_key = ''
consumer_secret = ''
access_token_key = ''
access_token_secret = ''

api = TwitterAPI(consumer_key, consumer_secret, access_token_key, access_token_secret)

@login_required
def feed(request):
	r = api.request('search/tweets', {'q':'#carnival', 'filter':'images'})

	url_list = []
	retweet_count_list = []
	url_retweet_dict = {}

	for item in r:
		line = str(item)
		pos = line.find('media_url_https')
		t = line[pos + 21:].find('\'')
		if(pos >= 0):
			url = line[pos + 20:pos + 21 + t]
			url_list.append(str(url))

		retweet_pos = line.find('retweet_count')
		t = line[retweet_pos:].find(',')
		if(retweet_pos >= 0):
			count = line[retweet_pos + 16:retweet_pos+ t]
			retweet_count_list.append(int(count))

	size = len(url_list)

	for i in range(0,size):
		url_retweet_dict[url_list[i]] = retweet_count_list[i]

	url_list_in_database = Album.objects.all().filter(user = request.user).values('image_url')

	temp = []
	for url in url_list_in_database:
		temp.append(str(url['image_url']))

	url_list_in_database = temp

	new_urls = list(set(url_list) - set(url_list_in_database))

	for url in new_urls:
		album = Album(image_url = url, user = request.user, retweet_count = url_retweet_dict[url])
		album.save()

	temp = Album.objects.all().filter(user = request.user).values('image_url', 'time_added', 'retweet_count')	

	url_list = {}

	for entry in temp:
		dt = str(entry['time_added'])[0:10]
		dt = calendar.month_name[int(dt[5:7])] + " " + dt[8:10] + ", " + dt[0:4]
		url_list[str(entry['image_url'])] = (dt, str(entry['retweet_count']))

	# print url_list

	total_entries_in_database = len(url_list)

	return render(request, 'assignment/feed.html', {'url_list': url_list})

def register(request):
	context = RequestContext(request)
	registered = False
	if request.method == 'POST':
		user_form = UserForm(data=request.POST)
		
		if user_form.is_valid():
			user = user_form.save()
			user.set_password(user.password)
			user.save()
			registered = True
		else:
			print user_form.errors
	else:
		user_form = UserForm()
	return render_to_response(
			'assignment/register.html',
			{'user_form': user_form, 'registered': registered},
			context)

def user_login(request):
	context = RequestContext(request)
	if request.method == 'POST':
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(username=username, password=password)
		if user:
			if user.is_active:
				login(request, user)
				return HttpResponseRedirect('/')
			else:
				return HttpResponse("Your assignment account is disabled.")
		else:
			print "Invalid login details: {0}, {1}".format(username, password)
			return HttpResponse("Invalid login details supplied.")
	else:
		return render_to_response('assignment/login.html', {}, context)


@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/')
