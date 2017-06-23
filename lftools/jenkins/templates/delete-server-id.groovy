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
