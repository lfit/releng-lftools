// @License EPL-1.0 <http://spdx.org/licenses/EPL-1.0>
// #############################################################################
// Copyright (c) 2017 The Linux Foundation and others.
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Eclipse Public License v1.0
// which accompanies this distribution, and is available at
// http://www.eclipse.org/legal/epl-v10.html
//
// #############################################################################

import hudson.*
import hudson.maven.MavenModuleSet
import hudson.model.*
import hudson.util.ReflectionUtils;
import java.lang.reflect.Field;
import jenkins.*
import jenkins.model.*
import org.apache.commons.lang.RandomStringUtils
import com.cloudbees.plugins.credentials.impl.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.domains.*;
import org.jenkinsci.lib.configprovider.ConfigProvider
import org.jenkinsci.lib.configprovider.model.Config
import org.jenkinsci.plugins.configfiles.ConfigFilesManagement
import org.jenkinsci.plugins.configfiles.maven.GlobalMavenSettingsConfig.GlobalMavenSettingsConfigProvider
import org.jenkinsci.plugins.configfiles.maven.MavenSettingsConfig
import org.jenkinsci.plugins.configfiles.maven.security.ServerCredentialMapping
import org.jenkinsci.plugins.configfiles.maven.MavenSettingsConfig.MavenSettingsConfigProvider
import org.jenkinsci.plugins.configfiles.GlobalConfigFiles
import org.apache.commons.lang.RandomStringUtils
import org.jenkinsci.plugins.configfiles.ConfigFileStore
import org.jenkinsci.plugins.configfiles.ConfigFiles;

// Global variables
def projects = ["project-one":"one" , "project-two":"two" , "project-three":"three"]
def servers = ["releases", "staging", "site", "snapshots"]
GlobalConfigFiles globalConfigFiles = new GlobalConfigFiles();
ConfigFileStore storing = GlobalConfigFiles.get();

// ----- Function definitions -----

// Function to check if a credential exists or not
def findCredentials = { username ->
    def find_creds = com.cloudbees.plugins.credentials.CredentialsProvider.lookupCredentials(
        com.cloudbees.plugins.credentials.common.StandardUsernamePasswordCredentials.class,
        jenkins.model.Jenkins.instance
    )
    def c = find_creds.findResult { it.username == username ? it : null }
    if ( c ) {
        return true
    } else {
        return false
    }
}

// Function to create credentials
def createCredential = { project, password ->
    int randomPasswordLength = 64
    String charset = (('a'..'z') + ('A'..'Z') + ('0'..'9')).join()
    String randomPassword
    randomPassword = RandomStringUtils.random(randomPasswordLength, charset.toCharArray())
    boolean credExists = false
    Credentials cred
    println "creating credentials for ${project}"
    cred = (Credentials) new UsernamePasswordCredentialsImpl(CredentialsScope.GLOBAL,"${project}", "${project} Nexus deployment", "${project}", "${password}")
    SystemCredentialsProvider.getInstance().getStore().addCredentials(Domain.global(), cred)
}

// Function to map credentials to a config file
def mapConfig = { project ->
    MavenSettingsConfigProvider mavenSettingsProvider = new MavenSettingsConfigProvider();
    List<ServerCredentialMapping> mappings
    ServerCredentialMapping mapping
    println "Mapping credentials for ${project}"
    mappings = new ArrayList<ServerCredentialMapping>();
    for (serv in servers) {
        println "Adding server ${serv} to ${project}"
        if (serv.contains("10001")){
            mapping = new ServerCredentialMapping("${serv}", "docker");
        }else{
            mapping = new ServerCredentialMapping("${serv}", "${project}");
        }
        mappings.add(mapping);
    }
    println "Adding the config file for ${project}"
    MavenSettingsConfig c2 = new MavenSettingsConfig("${project}-settings", "${project}-settings", "${project}-settings", mavenSettingsProvider.loadTemplateContent(), MavenSettingsConfig.isReplaceAllDefault, mappings);
    globalConfigFiles.save(c2);
    storing.save(c2);
}

// ----- Function calls -----

// Full loop that creates credentials and config files with servers and credentials mapped
projects.each { proj, pass ->
    credExists=findCredentials("${proj}")
    if (credExists){
        println "Skipping ${proj}, credential exists"
    } else {
         createCredential("${proj}", "${pass}")
    }
    mapConfig("${proj}")
};
