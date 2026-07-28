---
layout: default
title: Wiki
navbar_title: Wiki
permalink: /wiki/
---

{% assign notes = site.pages | where: "public", true | sort: "date" | reverse %}
{% assign wiki_count = 0 %}
{% for note in notes %}
{% unless note.type == "paper-reading" %}
{% assign wiki_count = wiki_count | plus: 1 %}
{% endunless %}
{% endfor %}

<div class="row">
    <div class="col-lg-10 mx-auto">
        <div class="bg-white shadow-sm rounded-xl p-4 p-md-5">
            <h1 class="mb-2">Wiki</h1>
            <div class="paper-reading-meta mb-4">
                {{ wiki_count }} notes · selected from my Obsidian vault
            </div>

            <div class="wiki-list">
                {% for note in notes %}
                {% unless note.type == "paper-reading" %}
                <article class="wiki-list-item">
                    <div class="paper-note-topline">
                        {% if note.type %}
                        <span class="paper-note-category">{{ note.type | replace: "-", " " | capitalize }}</span>
                        {% endif %}
                        {% if note.date %}
                        <time class="paper-note-time" datetime="{{ note.date | date_to_xmlschema }}">
                            {{ note.date | date: "%Y-%m-%d" }}
                        </time>
                        {% endif %}
                    </div>
                    <h2 class="h5 mb-1">
                        <a href="{{ note.url | relative_url }}">{{ note.title }}</a>
                    </h2>
                    {% if note.description %}
                    <p class="text-muted mb-1">{{ note.description }}</p>
                    {% endif %}
                </article>
                {% endunless %}
                {% endfor %}
            </div>

            {% if wiki_count == 0 %}
            <div class="paper-empty-state">No public notes yet.</div>
            {% endif %}
        </div>
    </div>
</div>
