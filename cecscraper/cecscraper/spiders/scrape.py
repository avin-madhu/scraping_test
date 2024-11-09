import re
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

class CeconlineSpider(CrawlSpider):
    name = 'ceconline'
    allowed_domains = ['ceconline.edu']
    start_urls = ['https://ceconline.edu/']

    # Define rules to follow links within the specified path only
    rules = (
        Rule(LinkExtractor(allow=r'/.*'), callback='parse_page', follow=True),
    )

    def parse_page(self, response):
        # Extract the title of the page
        title = response.xpath(
            'normalize-space(//div[contains(@class, "title")]/text() | //h2[contains(@class, "custom_heading")]/text())'
        ).get()
        cleaned_title = self.clean_text(title)

        # Extract paragraphs (<p> tags) from the page
        paragraphs = response.xpath('//p/text()').getall()
        cleaned_paragraphs = [self.clean_text(p) for p in paragraphs]

        # Extract contact details (here only address bruh)
        address = response.xpath('//li[contains(@class, "contact-details__item_type_address")]/text()').get()
        phone = response.xpath('//li[contains(@class, "contact-details__item_type_tel")]/a/text()').get()
        email = response.xpath('//li[contains(@class, "contact-details__item_type_email")]/a/text()').get()

        # stm-contact-details__itemstm-contact-details__item stm-contact-details__item_type_fax
        contact_details = {}
        if address:
            contact_details['address'] = self.clean_text(address)
        if phone:
            contact_details['phone'] = self.clean_text(phone)
        if email:
            contact_details['email'] = self.clean_text(email)

        # Extract faculty details if present along wuth the HOD
        faculty,hod = self.parse_faculty_table(response)

        # Yield structured data as JSON
        data = {}
        if title:
            data['title'] = cleaned_title
        if faculty:
            data['faculty'] = faculty
        if hod:
            data['hod'] = hod
        if paragraphs:
            data['about'] = cleaned_paragraphs
        if contact_details:
            data['contact_details'] = contact_details
        yield data

    def parse_faculty_table(self, response):
        # Locate the faculty table based on the headers
        faculty_data = []
        faculty_table = response.xpath('//h3[span[contains(text(), "Faculty")]]/following-sibling::table')

        # scrape the hod data
        hod_section = response.xpath('//div[contains(@class, "stm-teacher-bio__content")]')
        if hod_section:
            hod_name = hod_section.xpath('.//strong[contains(text(), "Dr.") or contains(text(), "Sri.") or contains(text(), "Smt.")]/text()').get()
            hod_title = hod_section.xpath('.//span[contains(@style, "font-size: 12pt")]/text()').get()
            department_address = hod_section.xpath('.//p/text()').getall()
            department_address = [self.clean_text(line) for line in department_address if line.strip()]

            hod = {
                'name': hod_name,
                'title': hod_title,
                'address': ' '.join(department_address)
            }
        else:
            hod = None
        

        # Skip the header row and parse each faculty row
        rows = faculty_table.xpath('.//tr[position()>1]')
        for row in rows:
            name = self.clean_text(row.xpath('td[2]//text()').get())
            designation = self.clean(row.xpath('td[3]//text()').get())

            faculty_data_entry = {}
            if name:
                faculty_data_entry['name'] = name
            if designation:
                faculty_data_entry['designation'] = designation
            faculty_data.append(faculty_data_entry)

        return faculty_data,hod

    def clean_text(self, text):
        """Clean text by removing unnecessary spaces and non-ASCII characters."""
        cleaned_text = text.strip() if text else ''
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Remove excessive spaces
        cleaned_text = re.sub(r'[^\x00-\x7F]+', ' ', cleaned_text)  # Remove non-ASCII characters
        return cleaned_text
