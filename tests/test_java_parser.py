from app.java_parser import analyze_sources, join_path, strip_comments

CONTROLLER = """
package demo;
@RestController
@RequestMapping("/api/v1")
public class ItemController {
    private final ItemService itemService;
    public ItemController(ItemService itemService) { this.itemService = itemService; }

    @GetMapping
    public List<Item> list() { return null; }

    @PostMapping(path = {"/items", "/things"})
    public ResponseEntity<Map<String, String>> create(@RequestBody Item i) { return null; }

    @RequestMapping(value = "/old", method = {RequestMethod.PUT, RequestMethod.PATCH})
    public void legacy() {}

    // @DeleteMapping("/commented")
    public void nothing() {}
}
"""
SERVICE = "@Service\npublic class ItemService { }"


def test_endpoints_and_paths():
    _, endpoints, _ = analyze_sources({"ItemController.java": CONTROLLER, "ItemService.java": SERVICE})
    found = {(e["method"], e["path"]) for e in endpoints}
    assert found == {
        ("GET", "/api/v1"),
        ("POST", "/api/v1/items"),
        ("POST", "/api/v1/things"),
        ("PUT", "/api/v1/old"),
        ("PATCH", "/api/v1/old"),
    }
    assert all(e["controller"] == "ItemController" for e in endpoints)


def test_relationship_controller_to_service():
    _, _, rels = analyze_sources({"ItemController.java": CONTROLLER, "ItemService.java": SERVICE})
    assert any(r["source"] == "ItemController" and r["target"] == "ItemService" for r in rels)


def test_strip_comments_keeps_lines_and_strings():
    src = 'a // x\n"http://y" /* z\n */ b'
    out = strip_comments(src)
    assert out.count("\n") == src.count("\n")
    assert "http://y" in out and "x" not in out.split("\n")[0]


def test_join_path():
    assert join_path("/a/", "b") == "/a/b"
    assert join_path("", "") == "/"
