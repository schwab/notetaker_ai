# EDGE
#docker run -it -p 6399:6379 -p 7687:7687 -v /datadrive/redis_graph/notetaker_falkor_db/:/data  -e REDIS_ARGS="--dir /data --dbfilename dump.rdb" --name falkordb --rm falkordb/falkordb:edge
# MASTER
#docker run -it -p 6399:6379 -p 7687:7687 -v /datadrive/redis_graph/notetaker_falkor_db/:/data  -e REDIS_ARGS="--dir /data --dbfilename dump.rdb" --name falkordb --rm falkordb/falkordb:master
# 4.0.2 GA
docker run -it -p 6379:6379 -p 7687:7687 -v /datadrive/redis_graph/notetaker_falkor_db/:/data  -e REDIS_ARGS="--dir /data --dbfilename dump.rdb" --name falkordb --rm falkordb/falkordb:v4.0.2
#docker run` -it -`p 6379:6379 -v $(pwd):/data -e REDIS_ARGS="--dir /data --dbfilename dump.rdb" falkordb/falkordb:4.0.0-alpha.1
#docker run --name falkordb -p 6399:6379  -it falkor/falkordb:latest