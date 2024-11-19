# Mahala
# TODO
1) Implement MarketItemsView and Serializer
2) Devise some proper tests
3) Implement Item adding, removing and modifying views
4) 


## Dependencies
python >3.11.8   
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
#### 1) .env
Create `./backend/.env`
```
AWS_ACCESS_KEY_ID=<your minio access id>
AWS_SECRET_ACCESS_KEY=<your minio access key>
AWS_STORAGE_BUCKET_NAME=<your bucket name>
AWS_S3_URL=<http://127.0.0.1:9000> // replace with whatever port you're running the minio s3 on 
SECRET_KEY="secretkey"  // whatever django secret key 
GOOGLE_API_KEY="your google api key" //Obligatory
```
#### 2) MinIO S3 Local File Server
Media(item image files) are stored on a mock S3 compatible local file server with MinIO
Running MinIO server in a Docker container:
1) Install Docker
2) Run the MinIO container(on subsequent runs, the container will have been created and can be started with `docker start <container name>`)
```
docker run -p 9000:9000 -d -p 9001:9001 -e "MINIO_ROOT_USER=admin" -e "MINIO_ROOT_PASSWORD=minioadmin" -v ~/minio-data:/data quay.io/minio/minio server /data --console-address ":9001"
```
* Server will run on `127.0.0.1:9000`
* Minio admin console will run on `127.0.0.1:9001`
* Files will be stored locally in `~/minio-data` folder

#### 3) Run backend and add mock data
1) Migrate
Implements model changes on the database. Incremental, state-based. Do this if changes made to ./models.py. If questions are asked, better off deleting the migrations and the database then migrating again.  

```
   python manage.py makemigrations
   python manage.py migrate
```
run ```./migrate.sh``` as a shortcut
2) Create default superuser by loading a fixture with it set up

`python manage.py loaddata fixtures/admin.json`

3) Load categories
`fixtures/categories.json` defines the categories
`api/management/commands/` contains custom subcommands that can be invoked with `manage.py` as below
`python manage.py add_categories` will create records for every category in the file 

4) Run server
```python manage.py runserver```   
Shortcut ```./runserver.sh```

5) Add mock data

`python manage.py add_example_items`  will create some example items as given by `/fixtures/items.json`. **requires S3 server running** as it will also upload the corresponding images for the items

Log into Django admin portal on `http://127.0.0.1:8000/admin/` and add records as needed
Superuser details:

admin@mahala.us
admin

### Example data
#### Users
lady.day@gmail.com
pass1

john.coltrane@gmail.com
pass2

john.smith@gmail.com
pass3

flea@gmail.com
pass4

chad@gmail.com
pass5






