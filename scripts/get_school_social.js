#! /usr/bin/node
//  -*- coding: utf-8 -*-
//  >>
//      Copyright (c) 2016, Blake VandeMerwe - Vivint, inc.
//        Permission is hereby granted, free of charge, to any person obtaining
//        a copy of this software and associated documentation files
//        (the "Software"), to deal in the Software without restriction,
//        including without limitation the rights to use, copy, modify, merge,
//        publish, distribute, sublicense, and/or sell copies of the Software,
//        and to permit persons to whom the Software is furnished to do so, subject
//        to the following conditions: The above copyright notice and this permission
//        notice shall be included in all copies or substantial portions
//        of the Software.
//      big-data-2016, 2016
//  <<

var fs = require('fs');

var async = require('async');
var cheerio = require('cheerio');
var request = require('request');
var sqlite = require('sqlite3').verbose();

// start script
var db = new sqlite.Database('/tmp/rmp-db.sqlite');

// global vars
var social = [
    'youtube', 'twitter', 'facebook', 'plus.google',
    'instagram', 'pinterest'
];

db.all('SELECT id,name,url FROM school', function(err, rows) {
    async.filter(rows, function(row, callback) {
        callback(null, !!row.url);
    }, function(err, results) {
        async.eachLimit(results, 3, function(row, callback) {
            request(row.url, function(error, response, html) {
                if (error) {
                    console.log(error);
                } else {
                    var socialSites = {};

                    var $ = cheerio.load(html);

                    $('a').each(function(index, el) {
                        var href = $(this).attr('href') || null;

                        if (!href) {
                            return;
                        }

                        href = String(href).toLowerCase();

                        for (var idx in social) {
                            var site = social[idx];
                            if (href.indexOf(site+'.com') !== -1) {
                               socialSites[site] = href;
                            }
                        }
                    });
                    console.log(socialSites);
                }
                callback(null);
            });
        });
    });
});
