// @License EPL-1.0 <http://spdx.org/licenses/EPL-1.0>
// #############################################################################
// Copyright (c) 2014, 2017 The Linux Foundation and others.
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Eclipse Public License v1.0
// which accompanies this distribution, and is available at
// http://www.eclipse.org/legal/epl-v10.html
//
// Contributors:
//   Jessica Wagantall
// #############################################################################

import org.jenkinsci.lib.configprovider.AbstractConfigProviderImpl
import org.jenkinsci.lib.configprovider.ConfigProvider
import org.jenkinsci.lib.configprovider.model.Config
import org.jenkinsci.lib.configprovider.model.ContentType
import org.jenkinsci.lib.configprovider.model.ContentType.DefinedType
import jenkins.*
import jenkins.model.*
import hudson.*
import hudson.model.*
import org.jenkinsci.plugins.*
import org.jenkinsci.lib.configprovider.model.Config
import hudson.maven.MavenModuleSet
import org.jenkinsci.plugins.configfiles.ConfigFilesManagement
import org.jenkinsci.plugins.configfiles.maven.GlobalMavenSettingsConfig
import org.jenkinsci.plugins.configfiles.maven.GlobalMavenSettingsConfig.GlobalMavenSettingsConfigProvider
import org.jenkinsci.plugins.configfiles.maven.MavenSettingsConfig
import org.jenkinsci.plugins.configfiles.maven.security.ServerCredentialMapping;
import org.jenkinsci.plugins.configfiles.maven.MavenSettingsConfig.MavenSettingsConfigProvider
import com.cloudbees.plugins.credentials.impl.*;
import com.cloudbees.plugins.credentials.*;
import com.cloudbees.plugins.credentials.domains.*;
import org.jenkinsci.plugins.configfiles.GlobalConfigFiles;
import org.apache.commons.lang.RandomStringUtils
// TODO: Not all these imports are needed, organize them. 

println "printing all the credentials ..."
def creds = com.cloudbees.plugins.credentials.CredentialsProvider.lookupCredentials(
    com.cloudbees.plugins.credentials.common.StandardUsernameCredentials.class,
    Jenkins.instance,
    null,
    null
);
for (c in creds) {
     println(c.id + ": " + c.description)
}

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

println "Loop with credentials"
// Definitions needed for credentials
def projects = ["policy-docker", "policy-common", "policy-engine"]
int randomPasswordLength = 64
String charset = (('a'..'z') + ('A'..'Z') + ('0'..'9')).join()
String randomPassword
boolean credExists = false
Credentials cred

// Definitions needed for the config files
def instance = Jenkins.getInstance()
MavenSettingsConfigProvider mavenSettingProvider;
ConfigFilesManagement config_2;
GlobalMavenSettingsConfigProvider globalMavenSettingsConfigProvider;
def servers = ["ecomp-releases", "ecomp-staging", "ecomp-site"]
MavenSettingsConfigProvider mavenSettingsProvider = new MavenSettingsConfigProvider();
List<ServerCredentialMapping> mappings
ServerCredentialMapping mapping
MavenSettingsConfig c1
MavenSettingsConfig c2
GlobalConfigFiles globalConfigFiles = new GlobalConfigFiles();

// Full loop that creates credentials and config files with servers and credentials mapped
for (proj in projects) {
  randomPassword = RandomStringUtils.random(randomPasswordLength, charset.toCharArray())
  credExists=findCredentials("${proj}")
  if (credExists){
    println "Skipping ${proj}, credential exists"
  } else {
    println "creating credentials for ${proj}"
    cred = (Credentials) new UsernamePasswordCredentialsImpl(CredentialsScope.GLOBAL,"${proj}", "${proj}", "${proj}", "${randomPassword}")
    SystemCredentialsProvider.getInstance().getStore().addCredentials(Domain.global(), cred)
  }
  println "Mapping credentials for ${proj}"
  mappings = new ArrayList<ServerCredentialMapping>();
  for (serv in servers) {
    println "Adding server ${serv} to ${proj}"
    mapping = new ServerCredentialMapping("${serv}", "${proj}");
    mappings.add(mapping);
  }
  println "Adding the config file for ${proj}"
  c1 = (MavenSettingsConfig) mavenSettingsProvider.newConfig();
  c2 = new MavenSettingsConfig("${proj}", "${proj}" , c1.comment, c1.content, MavenSettingsConfig.isReplaceAllDefault, mappings);
  //MavenSettingsConfigProvider.getInstance().getStore().addConfig(next, dumy);
  globalConfigFiles.save(c2);
}

// Old test loop 
for (ConfigProvider cp : ConfigProvider.all()) {
    Config config = cp.newConfig("myid", "myname", "mycomment", "mycontent");
    def string_id = config.content;
    //println "add! ${string_id}"
}
