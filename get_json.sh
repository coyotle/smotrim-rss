#!/bin/bash

LIMIT=100

yq e '.[] | select(.brand_id != null) | .brand_id' podcasts.yaml | while read -r brand_id
do
    echo "Get json for brand: $brand_id"
    url="https://smotrim.ru/api/audios?brandId=$brand_id&page=1&limit=$LIMIT"
    
    curl -s "$url" > ./docs/data/brands/$brand_id.json
done

yq e '.[] | select(.rubric_id != null) | .rubric_id' podcasts.yaml | while read -r rubric_id
do
    echo "Get json for rubric: $rubric_id"
    url="https://smotrim.ru/api/audios?rubricId=$rubric_id&page=1&limit=$LIMIT"
    
    curl -s "$url" > ./docs/data/rubrics/$rubric_id.json
done
