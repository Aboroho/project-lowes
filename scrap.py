import os
import sys
import threading
from BrowserInstance import BrowserInstance
from pathlib import Path
import pandas as pd
import json
import re
from playwright.sync_api import sync_playwright


def get_product_data(data):
    product_obj = json.loads(data)
    product_details = product_obj['productDetails']
    product = list(product_details.items())[0][1]['product']
    modelId = product['modelId']

    return {
        'product_obj' : product_obj,
        'product_details' : product_details,
        'product' : product,
        'model_id' : modelId

    }

def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"[{file_path}] delted...")

def delete_product_json_file(model_id):
    if not model_id:
        print('No model_id provide')
        return
    path = Path(f'./data/{model_id}.json')
    delete_file(path)

def handle_product_data(data):
    
    try:
        product_data = get_product_data(data)
        product_obj = product_data['product_obj']
        model_id = product_data['model_id']

        path = Path(f'./data/{model_id}.json')
        if not (path.exists() and path.stat().st_size > 0):
            with open(path, 'w') as file:
                json.dump(product_obj, file, indent=4) 
                print(f'[{model_id}] data collected..')
                
    except Exception as e:
        delete_product_json_file(model_id)
        print(f'Error : {e} | will retry later')




def handle_browser(playwright):
    

    baseUrl = "https://www.lowes.com/search?searchTerm="

    csv = pd.read_csv('./product_data.csv')
    product_ids = csv.iloc[:,3].to_list()

    # url pattern
    json_url_pattern =  re.compile(r'https://www\.lowes\.com/wpd/.*/productdetail/.*')
    base_url_pattern = re.compile(rf'{re.escape(baseUrl)}.*')

    
   
    retry_count = 0
    unresolved_models = {}


    def clear_unresolved_models():
        print('clearing before exiting...')
        for model_id, status in unresolved_models.items():
            print(f"{model_id}  :  {status}")
            if (status == 2):
                delete_product_json_file(model_id)




    def close_browser_and_retry():
        clear_unresolved_models()
        sys.exit(2)


    def request_handler(route, request):
        model_id = request.headers.get('x-model_id', None)
        request_url = request.url
        
        if (base_url_pattern.match(request_url)):
            print(f'\nSearching for : {model_id}')

        if (json_url_pattern.match(request_url)):
            if (unresolved_models.get(model_id, None) == 3):
                route.abort()
                return
            unresolved_models[model_id] = 2

        try:
            route.continue_()
        except:
            print(str(e))

    

    def response_handler(response):
        nonlocal unresolved_models
        request_url = response.request.url
        response_url = response.url
        status = response.status
        model_id = response.request.headers.get('x-model_id', None)

        file_path = Path(f'./data/{model_id}.json')

        if (base_url_pattern.match(request_url)):
            print(f'response for [{model_id}]')
            if (status == 403):
                print(f'{status}:[{model_id}] | {request_url}')
                unresolved_models[model_id] = 2
                close_browser_and_retry()
                return
            
            with open(file_path, 'w') as file:
                    file.write('')

            unresolved_models[model_id] = 1

        elif (json_url_pattern.match(response_url)):
            try:
                if status != 200:
                    print(f'{status} : {request_url}')
                    close_browser_and_retry()
                    return
                
                data =  response.body()
                response_thread = threading.Thread(target=handle_product_data, args=(data,))
                response_thread.start()
                
                unresolved_models[model_id] = 3
                print(f'data collected : {response_url}' )
            except Exception as e:
                delete_product_json_file(model_id)

           

    

    def run(browser_instance,product_ids, start_index = 0):
        search_empty_file = False
        if(len(sys.argv) > 1):
            if (sys.argv[1] == "-e"):
                search_empty_file = True
        
        print(search_empty_file)
        page = browser_instance.get_page()
        print(f'instance id : {browser_instance.id}')

         # attaching handler
        browser_instance.on_request_handler (request_handler)
        browser_instance.on_response_handler( response_handler)

        
        nonlocal retry_count

        id_count = len(product_ids)
        for index in range(start_index, id_count):   
               
            id = product_ids[index]
            try:
                file_path = Path(f"./data/{id}.json")
            
                if  (file_path.exists()):
                    if os.stat(file_path).st_size != 0:
                        continue
                    else:
                        if not search_empty_file:
                            continue

                # print(f'[{id}] Skipping.... | Data is already collected or No data is available!')
                
            except Exception as e:
                print(f"Error: Something with file handling at line 104")
                return

       
            try:
                
                page.set_extra_http_headers({
                    'x-model_id': id,
                })
                page.goto(f"{baseUrl}{id}")
                # Clear localStorage
                page.evaluate("window.localStorage.clear();")
                # # Clear sessionStorage
                page.evaluate("window.sessionStorage.clear();")

                # if retry_count > 0:
                #     retry_count = 1
                # page.wait_for_load_state("load")
            except Exception as e:
                # if "Target page, context or browser has been closed" in str(e):
                #     return 
                print(f'Error during accessing the web:\n======================\n {str(e)}')
                close_browser_and_retry()
                return
                
                 
            
                
                


    
    
    def start_collecting_data(start_index = 0, current_model_id = None):
        if retry_count == 0:
            print('Start collecting data...')
        else:
            print(f'Retry count:{retry_count}\nRetrying from [{product_ids[start_index]}]')


        print('data fetching started....')
        browser_instance = BrowserInstance(playwright)
        run(browser_instance, product_ids, start_index)

    #executing  with start_index
    start_collecting_data(5520)

    
    



with sync_playwright() as playwright:
    
    try:
        handle_browser(playwright)
    except Exception as e:
        print(str(e))