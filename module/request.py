import cgi

class Request:
    @staticmethod
    def sanitize(input_date):
        if isinstance(input_date,list):
            return [Request.sanitize(item) for item in input_date]
        else:
            input_date = input_date.strip()
            input_date = cgi.escape(input_date,quote=True)
            return input_date
    
    @staticmethod
    def request(key):
        request = {k.lower(): v for k,v in (cgi.FieldStorage()).items()}
        return Request.sanitize(request[key]) if key in request else None

    @staticmethod
    def get(key):
        get_request = {k.lower(): v for k,v in (cgi.FieldStorage()).items() if k.lower() == 'get'}
        return Request.sanitize(get_request[key]) if key in get_request else None

    @staticmethod
    def post(key):
        post_request = {k.lower(): v for k,v in (cgi.FieldStorage()).items() if k.lower() == 'post'}
        return Request.sanitize(post_request[key]) if key in post_request else None