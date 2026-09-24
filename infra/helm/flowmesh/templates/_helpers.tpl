{{/*
Expand the name of the chart.
*/}}
{{- define "flowmesh.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "flowmesh.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "flowmesh.labels" -}}
helm.sh/chart: {{ include "flowmesh.name" . }}-{{ .Chart.Version | replace "+" "_" }}
{{ include "flowmesh.selectorLabels" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "flowmesh.selectorLabels" -}}
app.kubernetes.io/name: {{ include "flowmesh.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
