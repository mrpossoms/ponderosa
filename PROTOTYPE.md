# Ponderosa Fire Protection Prototype Architecture

Ponderosa fire protection is an AI first fire mitigation service which seeks to help users (particularly those in the WUI) audit their properties for highly localized fire risk.

## Flow

The audit will work in the following way:
1. User makes an account
2. User walks the perimeters of their buildings recording video/data
3. User recording is uploaded to the server
4. Server processes data facilitated by a multi-modal LLM provider
5. LLM produces list of suggestions given custom system prompt and user imagery
6. list of suggestions are processed into UI
	a. Highlights the trouble areas
	b. video frame for context
	c. suggestion of how to address it
	d. recommended affiliate links for local companies who can perform the service
7. User recieves an email to their suggestion page

## Components

### Client

* Static web-page
* location: `site/root/var/www/html/app.html`
* global url: app.ponderosafireprotection.com
* html page, no web-framework. All vanilla javascript and custom styles
* Guides user through the process of recording their property
	* Prompts the user with instructions live
	* Captures video using getUserMedia + <canvas>
	* User motion captured with DeviceMotion events
	* User location captured using Geolocation API
	* Client does some image processing to attempt to identify frames worth sending to server
		* Uses device pose + variance of the Laplacian to identify unique frames
		* Scoring runs on a downsampled grayscale copy of the frame for performance; full-res frame is captured separately for transmission
		* Sharpness threshold is adaptive: 75th percentile of a rolling window of recent scores, so it self-calibrates across lighting conditions
		* A time-based cooldown (e.g. 2s) between sends prevents burst-sending when a scene suddenly sharpens
		* Frames are JPEG-encoded via canvas.toBlob() before POST to minimize payload size
* Once data has been recorded it should be uploaded to the intake service
* Should generate survey ID as a geohash

### Intake

* Server side API which the client interacts with to upload user data
* Python package
* located: `services/intake`
* global url: api.ponderosafireprotection.com
* Runs as a daemon on webserver
* RESTful API design
	* routes
		* POST: survey/<id>/image/<img-id>
			* Uploads a frame from the recording with a given id for the user's survey session
		* POST: survey/<id>/trajectory
			* Uploads a json file containing the path user visited while recording
			* lat-lon coordinates
			* orientation information
			* references to image frames corresponding to poses
			* contains other user data such as email any text they submitted 
			* submission of trajectory creates a processing job in a work queue which can be accessed by other services. For now, the queue can simply be directories on the FS, each survey should be a directory named as its survey id.
				* writes survey id to named pipe to inform recommender

### Recommender

* Python package
* located: `services/recommender`
* Runs as a daemon on webserver
* Watches intake work queue directory
* Listens for messages on a named pipe for ready surveys
* Uses an LLM provider to process data
	* For now, the provider will be claude
	* Pass context file to LLM provider
		* gives prompt for how to identify trouble areas in image
		* Enumerates a list of actions that could be taken for selection as recommendations
	* Each image is passed along sequentially along with geolocation and orientation information to model
		* Model asseses data for each image + pose pair
	* Generate recommendation message is then passed to the model
	* LLM generates MD file of summary and recommended action selections for each image + pose pair
* Moves survey from work queue to processed directory
	* Stores output MD in survey directory
	* Signals presenter with survey ID via named pipe

### Presenter

* Python package
* Listens to named pipe for messages from the recommender
* Takes LLM recommendation MD file and processes it into a user readable UI
* Generates HTML page from recommendation
* Stores html page in directory isolated from the rest of the static site.
* Surveys accessible at surveys.ponderosafireprotection.com/<id>