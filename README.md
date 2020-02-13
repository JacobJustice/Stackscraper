# Stackscraper
A web scraper that scrapes the stackoverflow job listings for job data.
Built for my data collection and visualization class.


# Introduction
This program automatically scrapes the stackoverflow job listings.

The web page is formatted as such:
```
listings page that contains up to 25 listings:
    25 listings that contain the data
    ...
    ...
    
link to the next page (if there is one)
```

The scraper first goes across each listings page and gathers links
to each individual listing, storing them in a set. Once the links to all the 
listings have been collected then the scraper visits each link and 
parses it for the data.

Something interesting I've noticed is that stackoverflow will usually display 
to me about 3000 job listings (as of feb 13 2020). This results in about 125 pages of job listings
since there are 25 listings per page. The web scraper however is able to access much much more,
the last time I ran it it reached page 728 before exiting because there was no link to the next
page. This is more of a feature than a bug because I assume stackoverflow will only show me 
a filtered list of job listings based on some aspect of metadata my web browser is sending.


# Tools used
Scrapy

BeautifulSoup

Dictwriter/csv


# Attributes Stackscraper gathers:
Company name: Name of the company

Job type: Whether the job is full-time or part-time

Job Title: Name of the job that the listing is for

*Company Size: an approximate range of the size of the company in people

*Company Type: Public or private

*Role: A title describing the job more specifically

*Industry: what industry the job is a part of

*Experience level: level of experience the job requires

Location: Where the job is located

Technologies: What technologies the future employee would need to know to do the job

Likes: aggregate counter of how many users "Liked" the job listing

Dislikes: aggregate counter of how many users "Disliked" the job listing

Hearts: aggregate counter of how many users "Hearted" the job listing

Description: raw text of the job description
 
*not in every job listing; defaults to N/A


You could use this data to visualize which programming skills are in demand
in different parts of the world. You could also process the description
to try and fill in the other fields that employers often leave blank.
