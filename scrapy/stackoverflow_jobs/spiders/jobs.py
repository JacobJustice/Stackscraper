import scrapy
from csv import DictWriter
from bs4 import BeautifulSoup

from urllib.request import urlopen

'''
 @author: Jacob Justice

 This program automatically scrapes the stackoverflow job listings.
 The listings are formatted as such:
     there is a listings page that contains 25 listings:
         each listing contains the data I want to scrape
     the listings page contains a link to the next page
 
 The scraper first goes across each listings page and gathers links
 to each individual listing. Once the links to all the listings have been collected
 then the scraper visits each link and parses it for the data.

 Attributes I scrape:
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

 To exceed the minimum requirements I:
     scrape ~400 pages (more if you start at an earlier page)
     
     goes across multiple pages of the website as
     opposed to gathering links from one static page
    
     program knows when to stop scraping by checking
     if there is no chevron_right
     
     attributes I search for:
         next page url
         all job listing urls on a page
         job listing data (14 attributes total)
     
     filter the value of how many likes/dislikes/hearts
     to be stored as an int
     
     ensure there are no duplicate job listings stored
'''

class JobSpider(scrapy.Spider):
    name = "jobs"
    base_url = "https://stackoverflow.com"
    page_urls = []

    write_obj = open("stackoverflow_jobs.csv","a+")
    field_names = [
    'job title',
    'company_name',
    'company_size',
    'company_type',
    'role',
    'industry',
    'experience_level',
    'location',
    'job type',
    'technologies',
    'likes',
    'dislikes',
    'hearts',
    'url',
    'description'
    ]
    dict_write = DictWriter(write_obj, fieldnames=field_names)

    unique_job_listings = set()

    def start_requests(self):
        url = "https://stackoverflow.com/jobs?sort=p&pg=711"
        yield scrapy.Request(url=url, callback=self.gather_pages)

    def gather_pages(self, response):
        bs = BeautifulSoup(response.body, 'html.parser')

        mat_icons = bs.find_all(class_='material-icons')
        if mat_icons[-1].get_text() == "chevron_right":
            page_url = self.base_url + mat_icons[-1].parent.get('href')
        else:
            page_url = None

        links = bs.find_all(class_='mb4 fc-black-800 fs-body3')
        for link in links:
            href = link.a.get('href')
            self.unique_job_listings.add(href)
            #yield {"href": href}

        print("number of listings",len(self.unique_job_listings))

        if page_url != None:
            self.page_urls.append(page_url)
            yield scrapy.Request(url=page_url, callback=self.gather_pages)
        else:
            for url in self.unique_job_listings:
                listing_url = self.base_url + url
                yield scrapy.Request(url=listing_url, callback=self.gather_listing_info)

    def gather_listing_info(self, response):
        listing_info_dict = self.stackoverflow_job_info(response.url)

        if listing_info_dict != None:
            self.dict_write.writerow(listing_info_dict)
            yield listing_info_dict

    def stackoverflow_job_info(self, url):
        output = {}
        try:
            with urlopen(url) as fp:
                bs = BeautifulSoup(fp, 'html.parser')
        except:
            return None

        #company name
        #
        company_name = bs.find(class_='fc-black-700')
        if company_name.a != None:
            company_text = company_name.a.get_text().strip()
            output.update({'company_name':company_text})
        else:
            company_text = company_name.text
            company_text = company_text[:company_text.find('–')].strip().replace('\r', '').replace('\n', '')
            output.update({'company_name':company_text})


        #job type
        #company size
        #company type
        #role
        #industry
        #experience_level
        #
        items = bs.find(id='overview-items')
        mb8 = bs.find_all(class_='mb8')
        mb8_text = [x.get_text() for x in mb8]

        job_type = 'N/A'
        company_size = 'N/A'
        company_type = 'N/A'
        role = 'N/A'
        industry = 'N/A'
        experience_level = 'N/A'
        for i, text in enumerate(mb8_text):
            if 'Job type:' in text:
                job_type = text[len('Job type: '):]
            elif 'Company size:' in text:
                company_size = text[len('Company size: '):]
            elif 'Company type:' in text:
                company_type = text[len('Company type: '):]
            elif 'Role:' in text:
                role = text[len('Role: '):]
            elif 'Industry:' in text:
                industry = text[len('Industry: '):]
            elif 'Experience level:' in text:
                experience_level = text[len('experience level: '):]

        output.update( {'job type' : job_type.strip().replace('\r', '').replace('\n', '')} )
        output.update( {'company_size' : company_size.strip().replace('\r', '').replace('\n', '')} )
        output.update( {'company_type' : company_type.strip().replace('\r', '').replace('\n', '')} )
        output.update( {'role' : role.strip().replace('\r', '').replace('\n', '')} )
        output.update( {'industry' : industry.strip().replace('\r', '').replace('\n', '')} )
        output.update( {'experience_level' : experience_level.strip().replace('\r', '').replace('\n', '')} )


        #technologies
        #
        technologies = []

        technologies_tag = None
        for tag in bs.find_all(class_='fs-subheading mb16'):
            if tag.get_text() == 'Technologies':
                technologies_tag = tag

        if technologies_tag != None:
            for tech in technologies_tag.parent.find_all(class_='post-tag job-link no-tag-menu'):
                technologies.append(tech.get_text().replace('\r', '').replace('\n', ''))

        output.update({'technologies' : technologies})

        #job title
        #
        output.update({'job title':bs.find(class_='fc-black-900').get_text().replace('\r', '').replace('\n', '')})

        #location
        #
        location = (bs.find(class_='fc-black-500').get_text().strip())
        location = location[3:].replace('\r', '').replace('\n', '')
        output.update({'location':location})

        #likes
        #
        output.update({"likes":int(bs.select_one('svg.svg-icon.iconThumbsUp').parent.span.get_text())})

        #dislikes
        #
        output.update({"dislikes":int(bs.select_one('svg.svg-icon.iconThumbsDown').parent.span.get_text())})
        
        #hearts
        #
        output.update({"hearts":int(bs.select_one('svg.svg-icon.iconHeart').parent.span.get_text())})

        #url
        #
        output.update({"url":url})

        #description
        #
        mb16list = bs.find_all(class_ = "fs-subheading mb16")
        for i, tag in enumerate(mb16list):
            if tag.get_text() == "Job description":
                section_tag = mb16list[i].parent
        section_text = ""

        text_only = section_tag.find_all(text=True)
        del text_only[:2]

        for tag in text_only:
            section_text += tag.replace('\r', ' ').replace('\n', ' ')
        output.update({'description':section_text})

        return output
