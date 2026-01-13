## ShadingLanguageX (SLX) MaterialX Integration

### Design Goals

- Introduce a data-driven shading language. 
- Separability of tooling from runtime components
- Provide a formal specification of the language (assuming targeted to pass ISO standards)
- Provide syntax validation (e.g. EBNF)
- Provide semantic validation (e.g. type checking)
- Support transformations to / from MaterialX data model and shading language model ("compile" / "decompile")
- Support for node definitions from different versions of the "standard library" (See implementation details)
- Support for custom node definitions for user libraries.
- Support serialization of programs written in the shading language   
  - Requirement for versioning to allow this to be an archival format.
  - MIME Tagging such as "application/x-shadinglanguage"
- Support in "native" programming language support for MaterialX
- Exposure of interfaces for serialization across existing and future programming language APIs
- Provide API interfaces for validation.
- Command line support

- Future looking:
  - Generalize shading language interfaces so that other languages can use the same interfaces with different syntax (e.g., OSL).
  - Exposure of shading language constructs for use in other contexts.
  - Bi-directional transformation equivalence checking. This may or may not be possible.
  - Provide 1:1 mapping with all MaterialX node graph characteristics. This may or may not be possible.
  - Add support for editability of language at runtime (tooling). (See current interactive editor which is being developed at time of writing)

### Implementation Notes

- Definition Libraries:
    - Ideally the implementation conditionally compile/decompile using any version of the MaterialX definitions as it dynamically references the standard library at runtime. It would be beneficial maintain this *decoupling*. i.e. The language component can 
    still accept different library versions as input. This may be hard to due in practice since the component is built with a
    specific MaterialX version. e.g. if you release with version 1.39.5 it cannot be easily used with 1.39.3 since the
    runtime model may have changed.
    - It may be worthwhile to consider adding in a XML / JSON schema for node / function signature validation.
- Code Generation Representations:
    - The notion of "decompiling" from MaterialX closely matches the notion of "code generation". It
    would be worth to investigate the approach taken by SLX.
    - e.g. There is an existing runtime model which has similar characteristics to the core MaterialX representation and "ShaderGraph" representation. 
    - Multiple representations can incur, maintenance,  consistency and performance     
    - It is worthwhile to keep in mind thread safety of there is the desired to "compile" / "decompile" in parallel.
    - As with the existing code generation system, we want 
    SLX compile/decompile to be deterministic. (This could
    already be true, but would need to check). 
- Versioning:
    - Unless some upgrade mechanism is directly supported this must be done after conversion to the MaterialX runtime model.
    - As with current MaterialX documents validation may fail without an explicit patch version. (e.g. a function foo, has a new
    argument added between versions 1.39.5, and 1.39.5. If you write a program using the 1.39.5 version there is no way to validate it against the 1.39.5 runtime.)
- Deployment restrictions:
    - For greater interop compatibility, take into consideration restrictions on node graphs created via decompilation. e.g. to be compliant
    with USD restrictions. e.g. wrapping all functions as `nodedef`s including materials.
- Serialization:
    - For greater deployment compatibility, consider optional restrictions on language constructs allowed. e.g. usage of include, ad
    "library load" dependencies generally will not work for (non-desktop) e.g. Javascript, Rust deployment due to security restrictions.
    - Unify include / search path handling for XML vs SLX serialization.

### Implementation Layout
- Add a base shading language module: `MaterialXLanguage`
- Add a `MaterialXLanguageX` module which uses the base module.
- Add a wrapper for serialization.
  - If the desire is to formalize document serialization, then it would derive from a common serialization interface. e.g.
  - Add `DocumentSaver` and `DocumentLoader` to `MaterialXCore`
  - Add derivations `DocumentLoader` -> `SLXDocumentLoader`, and `DocumentSaver` -> `SLXDocumentSaver`.
    - Expose existing / future options for serialization.
- Add JS and Python bindings for the new modules / APIs.
    - Write command line tools for the new modules / APIs.
    - Layer tooling on top of the new modules / APIs. 
        - e.g. Python Interactive Editor.
        - Allow existing multiple version / library support at this level as versioned runtimes are required.