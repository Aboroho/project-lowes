import uuid
from dotenv import load_dotenv
import os

load_dotenv()

class BrowserInstance:
    _on_request_handler = None
    _on_response_handler = None
    
    _proxy  = {
        'server' : os.getenv('proxy-server'),
        'username' : os.getenv('proxy-username'),
        'password' : os.getenv('proxy-password')
    }
    
    def __init__(self,playwright, proxy = None, headless = False):
        config = {
            'headless' : headless,
            'proxy' : self._proxy
        }

        if proxy:
            config.proxy = proxy
        
        
        self.browser = playwright.firefox.launch(**config)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.id = str(uuid.uuid4())

        self.page.route("**/*", self.intercept_request)
        self.page.on("response", self.intercept_response)


    def clear(self):
        self.browser.close()
        
    def intercept_request(self, route, request):
        if self._on_request_handler is not None:
            self._on_request_handler(route, request)
        else:
            route.continue_()  # Continue with the request

    def intercept_response(self, response):
        if self._on_response_handler is not None:
            self._on_response_handler(response)

    def get_context(self):
        return self.context
    
    def get_page(self):
        return self.page
    
    def get_browser(self):
        return self.browser

   
    def on_request_handler(self, handler):
         self._on_request_handler = handler

    
    def on_response_handler(self, handler):
        self._on_response_handler = handler
    
   


