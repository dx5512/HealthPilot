"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import { getContacts, addContact, deleteContact } from "@/lib/api";
import type { ResidentContacts, ContactInfo } from "@/types";

export default function ContactsPage() {
  const { user } = useAuth();
  const userId = user?.user_id || "";
  const [contacts, setContacts] = useState<ResidentContacts | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newContact, setNewContact] = useState({ name: "", relation: "", phone: "", notify_method: "sms" });

  const loadContacts = useCallback(async () => {
    if (!userId) return;
    try {
      setContacts(await getContacts(userId));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    loadContacts();
  }, [loadContacts]);

  const handleAdd = async () => {
    if (!userId || !newContact.name || !newContact.phone) return;
    try {
      await addContact(userId, newContact);
      setShowAdd(false);
      setNewContact({ name: "", relation: "", phone: "", notify_method: "sms" });
      loadContacts();
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (contactId: string) => {
    if (!userId) return;
    try {
      await deleteContact(userId, contactId);
      loadContacts();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">👥 关联人管理</h1>
        <p className="mt-1 text-sm text-gray-500">绑定家属，异常时自动通知</p>
      </div>

      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">
            {contacts?.resident_name || user?.name || "我"}的关联人
          </h2>
          <button
            onClick={() => setShowAdd(true)}
            className="rounded-lg bg-primary px-4 py-2 text-sm text-white hover:bg-primary-dark"
          >
            + 添加关联人
          </button>
        </div>

        {contacts && contacts.contacts.length === 0 && !showAdd && (
          <p className="text-center text-gray-400 py-8">暂未添加关联人</p>
        )}

        {/* 关联人卡片 */}
        <div className="space-y-3">
          {contacts?.contacts.map((c: ContactInfo) => (
            <div
              key={c.id}
              className="flex items-center justify-between rounded-lg border border-gray-100 p-4"
            >
              <div>
                <p className="font-medium text-gray-900">
                  {c.name} <span className="text-sm text-gray-400">({c.relation})</span>
                </p>
                <p className="text-sm text-gray-500">
                  📱 {c.phone} · {c.notify_method === "sms" ? "短信" : c.notify_method === "wechat" ? "微信" : "站内信"}
                </p>
              </div>
              <button
                onClick={() => handleDelete(c.id)}
                className="rounded-lg border border-red-200 px-3 py-1.5 text-xs text-red-600 hover:bg-red-50"
              >
                删除
              </button>
            </div>
          ))}
        </div>

        {/* 添加表单 */}
        {showAdd && (
          <div className="mt-4 rounded-lg border border-primary/30 bg-primary/5 p-4">
            <h4 className="mb-3 font-medium text-gray-900">添加关联人</h4>
            <div className="grid grid-cols-2 gap-3">
              <input
                placeholder="姓名"
                value={newContact.name}
                onChange={(e) => setNewContact({ ...newContact, name: e.target.value })}
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
              />
              <input
                placeholder="关系（如：儿子、女儿）"
                value={newContact.relation}
                onChange={(e) => setNewContact({ ...newContact, relation: e.target.value })}
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
              />
              <input
                placeholder="手机号"
                value={newContact.phone}
                onChange={(e) => setNewContact({ ...newContact, phone: e.target.value })}
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
              />
              <select
                value={newContact.notify_method}
                onChange={(e) => setNewContact({ ...newContact, notify_method: e.target.value })}
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
              >
                <option value="sms">短信</option>
                <option value="wechat">微信</option>
                <option value="inapp">站内信</option>
              </select>
            </div>
            <div className="mt-3 flex gap-2">
              <button
                onClick={handleAdd}
                className="rounded-lg bg-primary px-4 py-2 text-sm text-white hover:bg-primary-dark"
              >
                确认添加
              </button>
              <button
                onClick={() => setShowAdd(false)}
                className="rounded-lg border border-gray-200 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
              >
                取消
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
