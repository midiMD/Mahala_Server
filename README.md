# Neighborly

# Dependencies
python 3.11.8   
```pip install -r backend/requirements.txt```  


## BackEnd
```cd backend```
### Migrations
Implements model changes on the database. Incremental, state-based. Do this if changes made to ./models.py. If questions are asked, better off deleting the migrations and the database then migrating again.  

```
   python manage.py makemigrations
   python manage.py migrate
```
run ```./migrate.sh``` as a shortcut

### Start server
```python manage.py runserver```   
Shortcut ```./runserver.sh``` 
