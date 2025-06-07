#!/bin/bash
set -e

NAMESPACE=${NAMESPACE:-default}
BLUE_DEPLOYMENT=chatapp-blue-chatapp
GREEN_DEPLOYMENT=chatapp-green-chatapp

# Wait for green deployment rollout
kubectl rollout status deployment/$GREEN_DEPLOYMENT -n $NAMESPACE

# Shift traffic fully to green
kubectl annotate service $GREEN_DEPLOYMENT traefik.ingress.kubernetes.io/weight=100 --overwrite -n $NAMESPACE
kubectl annotate service $BLUE_DEPLOYMENT traefik.ingress.kubernetes.io/weight=0 --overwrite -n $NAMESPACE

