//
//  RelativePathForScript.swift
//  Pyto
//
//  Created by Emma Labbé on 11/16/18.
//  Copyright © 2018-2021 Emma Labbé. All rights reserved.
//

import Foundation

/// Get the path for the given script relative to the Documents directory.
///
/// - Parameters:
///     - url: The full script's URL.
///
/// - Returns:
///     - The relative path.
func RelativePathForScript(_ url: URL) -> String {
    var filePath = url.path
    filePath = filePath.replacingFirstOccurrence(of: FileBrowserViewController.localContainerURL.path, with: "")
    if let iCloudPath = FileBrowserViewController.iCloudContainerURL?.path {
        filePath = filePath.replacingFirstOccurrence(of: iCloudPath, with: "iCloud/")
    }
    
    if filePath.hasPrefix("/private") {
        filePath = filePath.replacingFirstOccurrence(of: "/private", with: "")
    }
    
    if filePath.hasPrefix("/") && !FileManager.default.fileExists(atPath: filePath) {
        filePath.removeFirst()
    }
    
    return filePath
}
