# Further Explorations of Girder and HistomicsTK (Under Tulane Gleason Research)

##Overview
The Tulane Gleason project uses HistomicsTK as a tool to faciliate an easier experience for pathologists to annotate, perform analysis on biopsy images. We are mainly interested in using MongoDB database to store the resources that are uploaded onto Girder. Over the course of looking into Girder/HistomicsTK, we have several correspondances with David Manthey (david.mantehy@kitware.com) and Deepak Chittajallu (deepak,chittajallu@kitware.com) that has given us great guidance and insight into Girder/histomicsTK. We would like to share some of these informations with you. 

### Setting up 
Documented below are little features or settings that we have trouble finding:

#### Upload Images: 
Yes, we had trouble finding the upload button in the Girder interface. The resources and folders in Girder are only asseccible if the user s the authorization to do so. One can either make their own account (and have very specific privileges) or log in as the admin to have access to all the resources in that Girder instance (Please see 'Default Admin' for the default username and password). Once the user has the authorization to access a folder, the green upload button with an arrow pointing upwards will be on the upper-right side.

#### Default Admin
Every Grider instance comes with an admin account that has access to all the files and folders on that instance. The default account username is `admin`; the password is `password`. (Surprise!) 

#### Python_Girder Client
To interact with the Girder web API using python script, one can use the python library "Requests"; However, it is more convenient to use the Python-Girder Client library (which also uses the python requests library) made by the Kitware team.

### Using MongoDB (GridFS) as default Assetstore 
Girder uses GridFS schema to store the the large_image items as small packets in MongoDB database. (read more about Girder and GridFS)

#### Failure to open Images in HistomicsTK 
To store all the uploaded files into MongoDB, one has to create a MongoDB(GridFS) assetstore and set it as the default assetstore. AFter doing so, however, you would find that you can't open the files in HistomicsTK (It would return error message that reads: "please choose an large_image item"). Here is David's explanation:

```
The large_image plugin uses a variety of libraries to read images (OpenSlide, libtif, etc.).  These libraries use direct file access and don't natively have the ability to access non-filesystem assestores like GridFS or S3.  In order for large_image to use a non-filesystem assetstore, you need to configure a girder mount, and use a very recent version of the large_image plugin (more recent than the bundled version in HistomicsTK's docker file). 
```

Therefore, the user needs to conifgure a girder mount, see below (instruction by David) :

If you are using a docker from the HistomicsTK deploy_docker.sh where you added the ‘—latest’ flag, you should have the girder command:
` $ docker exec -it histomicstk_histomicstk bash`

```
ubuntu@histomicstk:/opt/histomicstk/girder$ girder
Usage: girder [OPTIONS] COMMAND [ARGS]...

  Girder: data management platform for the web.

Options:
  --version   Show the version and exit.
  -h, --help  Show this message and exit.

Commands:
  mount  † Warning: could not load plugin. See `girder mount --help`.
  serve  Run the Girder server.
  sftpd  Run the Girder SFTP service.
  shell  Run a Girder shell.
```

You have to install the ubuntu package for fuse:

` sudo apt-get update `  
` sudo apt-get install fuse `

And install the python dependencies for girder-mount:

`cd /opt/histomicstk/girder`
`sudo pip install .[mount]    # This is only because the docker installed girder globally`

You should git pull the latest large_image plugin if you dont have it :

`cd /opt/histomicstk/large_image/`
`git pull`

And then you can make a mount point via something like this

` mkdir /tmp/mountpoint`
` girder mount /tmp/mountpoint -d mongodb://mongodb:27017/girder`

At this step, if you see the `failed to mount FUSE` in red. You can fix that error by changing the permission the the folder /dev/fuse using `sudo chmod 777 <the file path>`. The /dev/fuse file can be found in the Docker instance of histomicstk_histomicstk whose bash shell can be entered using the first command found above.

At which point you should be able to use large_image with non-filesystem assetstores.

Remember to mount everytime you restart the Docker instance.

#### Using other MongoDB database location (other than in the default docker)

We asked David whether or not we can change the MongoDB database's location (to a different machine), here is David's answer:

The mongo process can definitely be put on another machine or run on the host machine rather than in a docker container.   When you use the deploy_docker.sh script, you can specify that `--mongo=docker` or `--mongo=host`.  If `--mongo=docker` is used (the default), you get the docker mongo container.  The database is stored in a directory, which could be specified via the --db parameter as a network directory.  If `--docker=host` is used, the script doesn't start a docker container.  Instead, it defaults to trying to use mongo on the host machine.  However, this is also configurable using the Girder configuration file.  For instance, you could specify a config file via --girder=cfg=(file) where that file contains 

```
[database]
uri = "mongodb://<some ip>:27017/girder"
```
Where the uri can be any mongo connection string.

Regarding speed -- the biggest data sent to and from Mongo tend to be the annotations, such as nuclei outlines.  For large annotations sets we often only get a subset, letting Mongo do the filtering, so this won't be too big a change.  A quick test on my local network adds about 5 seconds when writing 0.5 million nuclei, and the time reading then back doesn't feel much slower (but I haven't measured it).

## Building a new analysis pipeline

Here is Deepak's introduction on building an analysis funtionality:

```

-- The python API part of HistomicsTK with a bunch of atomic functions containing implementations of popular/well-cited/widely-used algorithms for some fundamental tasks such as color normalization, color deconvolution, nuclei detection, image-based feature extraction. Developers can contribute implementations of popular algorithms as a function in this API.

-- As a docker image containerizing a set of command-line executables (CLIs) that is pushed to Dockerhub. This uses the slicer_cli_web model as you rightly figured out. The slicer_cli_web_plugin(https://github.com/cdeepakroy/slicer_cli_web_plugin) serves as a good example of how to write CLIs in both Python and c++ and how to write the Dockerfile to package these CLIs into a docker container. The downside is this example maybe way too generic. For a more domain specific example, look at the CLIs (https://github.com/DigitalSlideArchive/HistomicsTK/tree/master/server) in HistomicsTK itself. Especially, the nuclei detection CLI(https://github.com/DigitalSlideArchive/HistomicsTK/tree/master/server/NucleiDetection) is a good example of how to write a CLI that uses dask to parallelize the analysis on a whole-slide image. This repo(https://github.com/cooperlab/NucleiCuts) is also a good example of how to create a docker image that derives from the HistomicsTK's docker image and encapsulates some CLIs (although there might be a few broken pieces but you should be able to grasp the structure). Following these examples as a template, you can create a docker image with your CLIs and push it to docker hub. We can then expose in the Analysis menu of HistomicsTK's web interface.

```

## Other