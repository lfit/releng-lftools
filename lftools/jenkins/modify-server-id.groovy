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

import org.jenkinsci.lib.configprovider.model.Config
import org.jenkinsci.plugins.configfiles.maven.MavenSettingsConfig
import org.jenkinsci.plugins.configfiles.maven.security.ServerCredentialMapping
import org.jenkinsci.plugins.configfiles.maven.MavenSettingsConfig.MavenSettingsConfigProvider
import org.jenkinsci.plugins.configfiles.GlobalConfigFiles
import org.jenkinsci.plugins.configfiles.ConfigFileStore

// Function to delete a server id on a config file
def removeServerId = { configFileId, serverId ->
    ConfigFileStore sto = GlobalConfigFiles.get();
    Config c = sto.getById("${configFileId}-settings");
    def string_id = c.name;
    def List<ServerCredentialMapping> map_list = c.serverCredentialMappings;
    println "These are the ServerIds for ${string_id} settings file: ${configFileId}-settings"
    //map_list.eachWithIndex { item, index ->
    //   println item.serverId;
    //}
    def indexToRemove;
    map_list.eachWithIndex { item, index ->
        if( item.serverId == serverId ) {
            println "Removing serverId " + item.serverId + " from config " + configFileId;
            indexToRemove = index;
        }
    }
    map_list.remove(indexToRemove);
    c.serverCredentialMappings = map_list;
}

// Function to add a server id on a config file
def addServerId = { configFileId, serverId ->
    List<ServerCredentialMapping> mappings
    ServerCredentialMapping mapping
    ConfigFileStore sto = GlobalConfigFiles.get();
    Config c = sto.getById("${configFileId}-settings");
    def string_id = c.name;
    def List<ServerCredentialMapping> map_list = c.serverCredentialMappings;
    println "Adding ${serverId} to ${string_id} settings file: ${configFileId}-setting"
    mappings = new ArrayList<ServerCredentialMapping>();
    mapping = new ServerCredentialMapping(serverId, configFileId);
    mappings.add(mapping);
    map_list.addAll(mappings);
    c.serverCredentialMappings = map_list;
}

// Function to modify a server id on a config file
def modifyServerId = { configFileId, oldServerId, newServerId ->
    println "Renaming serverId " + oldServerId + " to " + newServerId + " from config " + configFileId;
    removeServerId(configFileId, oldServerId)
    addServerId(configFileId, newServerId)
}

modifyServerId("new_project", "onap-site", "openecomp-site")
