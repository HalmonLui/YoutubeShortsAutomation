class DummyGoogleSheets:
    def open_by_url(self, url):
        return DummyWorksheet()

class DummyWorksheet:
    def sheet1(self):
        return self
    
    def get_all_records(self):
        return []  # Return empty list for spreadsheet mode

class DummyYouTubeService:
    def videos(self):
        return self
    
    def insert(self, **kwargs):
        return DummyRequest()

class DummyRequest:
    def execute(self):
        return {"id": "dummy_video_id"} 