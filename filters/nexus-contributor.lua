-- Credit the person who wrote a Nexus page when they are not the creator of
-- the content it describes. Reads the `nexus-contributor` front-matter field and adds
-- one line above the Comments section (or at the end of the page).

local function to_names(meta)
  if meta == nil then return {} end
  local items = (pandoc.utils.type(meta) == "List") and meta or { meta }
  local out = {}
  for _, v in ipairs(items) do
    local name = (pandoc.utils.type(v) == "table" and v.name) and v.name or v
    table.insert(out, pandoc.utils.stringify(name))
  end
  return out
end

local function join(names)
  if #names <= 1 then return names[1] end
  return table.concat(names, ", ", 1, #names - 1) .. " and " .. names[#names]
end

function Pandoc(doc)
  local names = to_names(doc.meta["nexus-contributor"])
  if #names == 0 then return nil end
  local line = pandoc.Div(
    pandoc.Para({ pandoc.Emph({ pandoc.Str("Nexus page by " .. join(names)) }) }),
    pandoc.Attr("", { "nexus-contributor" }))
  local at = #doc.blocks + 1
  for i, b in ipairs(doc.blocks) do
    if b.t == "Header" and pandoc.utils.stringify(b):lower() == "comments" then at = i; break end
  end
  doc.blocks:insert(at, line)
  return doc
end
