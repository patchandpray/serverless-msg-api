api_key = $(shell cat api_key)
api_id = $(shell cat api_id)
msg_id = $(shell cat ses_email)
aws_region = $(shell cat aws_region)
pwd = $(shell pwd)
store_secure = False

.PHONY: docker-build docker-run setup-env zip update get post cleanup

# Build Dockerfile
docker-build:
	docker build -t serverless-msg-api .

# Run Dockerfile
docker-run:
	docker run -it -v $(pwd):/app -v ${HOME}/.aws:/root/.aws serverless-msg-api:latest

# Setup AWS environment
setup-env:
	python3 setup_environment.py -e env_config.yml -z main.zip -c main.yml

# Targets for zipping and updating function code
zip:
	./create_code_object.sh

update:
	python3 upload_code.py -z main.zip -c main.yml -u

# Targets for testing API endpoints
get:
	curl -H 'X-Api-Key: $(api_key)' https://${api_id}.execute-api.$(aws_region).amazonaws.com/dev/msg?msg_id=$(msg_id)

post:
	curl -X 'POST' -H 'X-Api-Key: $(api_key)' 'https://$(api_id).execute-api.$(aws_region).amazonaws.com/dev/msg?msg_id=$(msg_id)&msg=Testing&subject=test_api&store_secure=$(store_secure)' 

cleanup:
	./cleanup.sh
