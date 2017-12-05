import praw
import pdb
import re
import os
import urllib.request
import bs4
from bs4 import BeautifulSoup
import time
import sys
import pprint

login_info = [os.environ['CLIENT_ID'], os.environ['CLIENT_SECRET'], os.environ['REDDIT_PASSWORD'], os.environ['REDDIT_USERNAME']]

reddit = praw.Reddit(client_id=login_info[0], 
client_secret=login_info[1], 
password=login_info[2], 
user_agent='Script for formatting WoBs, by /u/Torrieltar, v. 2.0', 
username=login_info[3])

comments_replied_to = []

subreddit = reddit.subreddit('Torrieltar')
num_comments = 15

while True:
	if len(comments_replied_to) < num_comments:
		for comment in reddit.redditor(login_info[3]).comments.new(limit=num_comments):
			if(comment.parent().id not in comments_replied_to):
				comments_replied_to.append(comment.parent().id)
	try:
		for reply in reddit.inbox.unread(limit=None):
			if reply.was_comment:
				footnote = 'https://www.reddit.com' + reply.context
			else:
				footnote = '***' + reply.subject + '***, PM from /u/' + reply.author.name
			reddit.redditor('Torrieltar').message('New Notification from WoB_Bot', reply.body + '\n\n***\n\n' + footnote)
			reply.mark_read()

		for comment in subreddit.comments(limit=num_comments):
			if comment.id not in comments_replied_to and not comment.author == "WoB_Bot":
				comment_text = comment.body
				bot_reply = ""
				for n in range(0, 3):
					url_start = re.search("wob.coppermind.net/events/([0-9a-zA-Z]|-)*/#e", comment_text, re.IGNORECASE)
					if url_start and re.search("wob_bot", comment.body, re.IGNORECASE):
						page_exists = True
						
						url_start = url_start.start()
						comment_text = comment_text[url_start:]
						url_end = re.search("#e", comment_text, re.IGNORECASE).start()
						arcanum_url = "https://" + comment_text[:url_end]
						comment_text = comment_text[url_end:]
						id_end = re.search("(?!([#|e|0-9]))", comment_text, re.IGNORECASE).start()
						arcanum_id = comment_text[1:id_end]
						
						try:
							page = urllib.request.urlopen(arcanum_url)        
						except urllib.error.HTTPError:
							try:
								from urllib.request import Request, urlopen
								req = Request(arcanum_url, headers={'User-Agent': 'Mozilla/5.0'})
								page = urlopen(req).read()
							except urllib.error.HTTPError:
								page_exists = False
								
						if page_exists:
							last = ""
							soup = BeautifulSoup(page, "html.parser")
							entry = soup.find("article", id=arcanum_id).find("div", class_="entry-content")
							for child in entry.children:
								if child.name == "h4":
									bot_reply = bot_reply + "\n\n**" + child.get_text(strip=True) + ":** "
									last = "h4"
								else:
									if last == "p":
										bot_reply = bot_reply + "\n\n"
									if type(child) is not bs4.element.NavigableString and type(child) is not bs4.element.Comment:
										bot_reply = bot_reply + child.get_text()
										last = child.name
									else:
										bot_reply = bot_reply + child
										last = "none"
							bot_reply = bot_reply + "\n\n[*Source.*](" + arcanum_url + "#" + arcanum_id + ")\n\n***\n\n"

					
				if(not(bot_reply == "")):
					bot_reply = bot_reply + "~WoB_Bot~"
					comment.reply(bot_reply)
				
					comments_replied_to.append(comment.id)
					if len(comments_replied_to) > num_comments:
						comments_replied_to.pop(0)
		time.sleep(30)
	except:
		e = sys.exc_info()[0]
		reddit.redditor('Torrieltar').message('WoB_Bot reported a failure in script execution.', 'WoB_Bot reported a failure in script execution: %s' % e)